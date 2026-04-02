"""WatchBot Agent brain: the core state machine that orchestrates calls.

Implements the complete call state machine:
IDLE -> GREETING -> ORDER_MATCHING -> ORDER_MATCHED -> GUIDING ->
  CONFIRMING/CORRECTING/HELPING -> NEXT_ITEM -> ... -> COMPLETED

Each state has timeout handling and fallback escalation.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Optional

from loguru import logger

from watchbot.config import AgentConfig
from watchbot.core import prompts
from watchbot.core.models import EventType, SessionState
from watchbot.core.schemas import PickingStep, VisionCheckResult
from watchbot.order.service import OrderService
from watchbot.telephony.call_manager import CallSession
from watchbot.vision.analyzer import VisionAnalyzer
from watchbot.vision.camera import CameraManager, CaptureMode


class AgentBrain:
    """The WatchBot Agent that handles a single call session.

    Coordinates between telephony (ASR/TTS), vision (camera + model),
    and order data to guide a rider through product picking.
    """

    def __init__(
        self,
        config: AgentConfig,
        call: CallSession,
        camera: CameraManager,
        vision: VisionAnalyzer,
        order_service: OrderService,
        warehouse_id: int,
        warehouse_name: str,
    ):
        self._config = config
        self._call = call
        self._camera = camera
        self._vision = vision
        self._order_service = order_service
        self._warehouse_id = warehouse_id
        self._warehouse_name = warehouse_name

        self._state = SessionState.IDLE
        self._order = None
        self._picking_route: list[PickingStep] = []
        self._current_item_index: int = 0
        self._state_entered_at: float = time.time()
        self._events: list[dict] = []

    @property
    def state(self) -> SessionState:
        return self._state

    def _transition(self, new_state: SessionState) -> None:
        """Transition to a new state, logging the change."""
        old = self._state
        self._state = new_state
        self._state_entered_at = time.time()
        self._log_event(EventType.STATE_CHANGE, {"from": old.value, "to": new_state.value})
        logger.info(f"State: {old.value} -> {new_state.value}")

    def _log_event(self, event_type: EventType, payload: dict) -> None:
        self._events.append({
            "type": event_type.value,
            "payload": payload,
            "time": datetime.now().isoformat(),
        })

    def _state_elapsed(self) -> float:
        """Seconds since entering current state."""
        return time.time() - self._state_entered_at

    @property
    def remaining_items(self) -> int:
        return len([s for s in self._picking_route if not s.confirmed])

    # -------------------------------------------------------------------
    # Main call handling loop
    # -------------------------------------------------------------------

    async def handle_call(self) -> dict:
        """Main entry point: handle the entire call lifecycle.

        Returns a summary dict of the session.
        """
        logger.info(f"Handling call from {self._call.caller_phone} at warehouse {self._warehouse_name}")

        # Start camera in burst mode for incoming call
        self._camera.set_mode(CaptureMode.BURST)

        try:
            # Phase 1: Greeting and order matching
            await self._phase_greeting()

            if self._state == SessionState.ESCALATED:
                return self._build_summary()

            # Phase 2: Guide through each item
            await self._phase_picking()

            # Phase 3: Wrap up
            if self._state != SessionState.ESCALATED:
                await self._phase_completed()

        except Exception as e:
            logger.error(f"Agent error: {e}")
            self._log_event(EventType.ERROR, {"error": str(e)})
            await self._call.speak("抱歉系统出了点问题，帮您转人工客服~")
            self._transition(SessionState.ESCALATED)

        finally:
            self._camera.set_mode(CaptureMode.IDLE)

        return self._build_summary()

    # -------------------------------------------------------------------
    # Phase 1: Greeting & Order matching
    # -------------------------------------------------------------------

    async def _phase_greeting(self) -> None:
        self._transition(SessionState.GREETING)
        await self._call.speak(prompts.greeting())

        # Wait for rider to say the order number
        self._transition(SessionState.ORDER_MATCHING)

        max_attempts = 3
        for attempt in range(max_attempts):
            rider_text = await self._call.listen()
            self._log_event(EventType.ASR_RESULT, {"text": rider_text})

            if not rider_text:
                if self._state_elapsed() > self._config.state_idle_timeout:
                    await self._call.speak(prompts.idle_check())
                    continue
                continue

            # Try to find the order
            order = await self._order_service.fuzzy_find_order(
                self._warehouse_id, rider_text
            )

            if order:
                self._order = order
                await self._order_service.mark_in_progress(order.id)
                self._log_event(EventType.ORDER_MATCHED, {
                    "order_id": order.platform_order_id,
                    "items": order.items_json,
                })

                # Build picking route
                from watchbot.core.models import Warehouse
                from sqlalchemy import select

                self._picking_route = await self._order_service.build_picking_route(
                    order, type("W", (), {"id": self._warehouse_id, "shelf_map_json": {}})()
                )

                self._transition(SessionState.ORDER_MATCHED)
                await self._call.speak(prompts.order_confirmed(order.total_items))
                return

            # Order not found
            await self._call.speak(prompts.cant_find_order())

        # Failed after max attempts
        await self._call.speak(prompts.escalate_to_human())
        self._transition(SessionState.ESCALATED)

    # -------------------------------------------------------------------
    # Phase 2: Guided picking
    # -------------------------------------------------------------------

    async def _phase_picking(self) -> None:
        """Guide the rider through each item in the picking route."""
        self._transition(SessionState.GUIDING)

        for idx, step in enumerate(self._picking_route):
            self._current_item_index = idx

            # Tell rider where to go
            guidance = prompts.guide_to_item(step)
            await self._call.speak(guidance)
            self._log_event(EventType.TTS_PLAYED, {"text": guidance})

            # Set camera to normal mode while walking
            self._camera.set_mode(CaptureMode.NORMAL)

            # Visual verification loop
            verified = await self._verify_item(step)

            if not verified and step.correction_count >= self._config.max_correction_attempts:
                await self._call.speak(prompts.escalate_to_human())
                self._transition(SessionState.ESCALATED)
                return

            step.confirmed = True
            self._log_event(EventType.ITEM_CONFIRMED, {
                "sku": step.sku,
                "corrections": step.correction_count,
            })

            # If more items remain, transition to NEXT_ITEM
            if idx < len(self._picking_route) - 1:
                self._transition(SessionState.NEXT_ITEM)

    async def _verify_item(self, step: PickingStep) -> bool:
        """Visual verification loop for a single item.

        Returns True if confirmed, False if max corrections exceeded.
        """
        self._camera.set_mode(CaptureMode.BURST)

        max_wait = 60  # seconds
        start = time.time()

        while time.time() - start < max_wait:
            # Check if we should capture a frame
            if not await self._camera.should_capture_now():
                await asyncio.sleep(0.3)
                continue

            # Capture and analyze
            frame_b64 = await self._camera.capture_frame_as_base64()
            if not frame_b64:
                # Camera unavailable, degrade to voice-only
                await self._call.speak(prompts.camera_unavailable())
                # Ask rider to confirm verbally
                rider_text = await self._call.listen()
                if rider_text:
                    return True  # Trust the rider in degraded mode
                continue

            self._log_event(EventType.FRAME_CAPTURED, {"size": len(frame_b64)})

            result = await self._vision.check_product(
                frame_base64=frame_b64,
                product_name=step.name,
                product_appearance=step.appearance,
                shelf_id=step.shelf_id,
                shelf_layer=step.shelf_layer,
            )
            self._log_event(EventType.VISION_RESULT, {
                "correct": result.correct,
                "wrong": result.wrong,
                "uncertain": result.uncertain,
                "confidence": result.confidence,
            })

            if result.correct:
                await self._call.speak(prompts.item_confirmed())
                return True

            if result.wrong:
                step.correction_count += 1
                self._log_event(EventType.ITEM_CORRECTED, {
                    "sku": step.sku,
                    "attempt": step.correction_count,
                })

                if step.correction_count >= self._config.max_correction_attempts:
                    return False

                self._transition(SessionState.CORRECTING)
                await self._call.speak(prompts.item_wrong_gentle(step))
                self._transition(SessionState.GUIDING)

            elif result.uncertain:
                if result.confidence < self._config.vision_confidence_threshold:
                    await self._call.speak(prompts.item_uncertain_ask(step))
                    rider_text = await self._call.listen()
                    if rider_text and any(w in rider_text for w in ["是", "对", "没错", "嗯"]):
                        return True

            # Small pause before next check
            await asyncio.sleep(0.5)

        # Timeout: ask rider
        await self._call.speak(prompts.idle_check())
        rider_text = await self._call.listen()
        return bool(rider_text)

    # -------------------------------------------------------------------
    # Phase 3: Completion
    # -------------------------------------------------------------------

    async def _phase_completed(self) -> None:
        self._transition(SessionState.COMPLETED)
        await self._call.speak(prompts.all_done())

        if self._order:
            await self._order_service.mark_completed(self._order.id)

    # -------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------

    def _build_summary(self) -> dict:
        return {
            "warehouse": self._warehouse_name,
            "rider_phone": self._call.caller_phone,
            "order_id": self._order.platform_order_id if self._order else None,
            "final_state": self._state.value,
            "items_total": len(self._picking_route),
            "items_confirmed": len([s for s in self._picking_route if s.confirmed]),
            "total_corrections": sum(s.correction_count for s in self._picking_route),
            "escalated": self._state == SessionState.ESCALATED,
            "transcript": self._call.transcript,
            "events": self._events,
        }

"""Phase 0 offline simulation: replay historical video + simulate a call.

Usage:
    python -m watchbot.scripts.simulate \
        --video path/to/video.mp4 \
        --order-file path/to/order.json

This simulates the full WatchBot flow without real telephony:
1. Reads frames from a local video file
2. Uses SimulatedASR with scripted rider responses
3. Uses SimulatedTTS that logs AI speech to console
4. Calls the real vision model API to analyze frames
5. Outputs a transcript log showing "what AI would have said"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from loguru import logger

from watchbot.config import load_config
from watchbot.core.agent import AgentBrain
from watchbot.core.database import close_db, init_db
from watchbot.core.schemas import OrderCreate, OrderItem
from watchbot.order.service import OrderService
from watchbot.telephony.asr import SimulatedASR
from watchbot.telephony.call_manager import CallSession
from watchbot.telephony.tts import SimulatedTTS
from watchbot.vision.analyzer import VisionAnalyzer
from watchbot.vision.camera import CameraManager


async def run_simulation(
    video_path: str,
    order_data: dict,
    rider_script: list[str] | None = None,
) -> dict:
    """Run a single offline simulation.

    Args:
        video_path: Path to the video file.
        order_data: Order JSON with warehouse_id, platform_order_id, items.
        rider_script: Simulated rider speech lines.

    Returns:
        Session summary dict.
    """
    config = load_config()
    await init_db(config)

    # Set up simulated telephony
    if rider_script is None:
        order_id = order_data.get("platform_order_id", "0000")
        rider_script = [
            f"取{order_id}号",
            "好的",
            "嗯",
            "对",
        ]

    asr = SimulatedASR(rider_script)
    tts = SimulatedTTS()

    call = CallSession(
        call_id="sim-001",
        caller_phone="13800000000",
        asr=asr,
        tts=tts,
    )

    # Set up camera from video file
    camera = CameraManager(config.vision)
    connected = await camera.connect(video_path)
    if not connected:
        logger.error(f"Cannot open video: {video_path}")
        return {"error": "video_not_found"}

    # Set up vision analyzer
    vision = VisionAnalyzer(config.vision)

    # Create the order in DB
    from watchbot.core.database import get_session_factory

    factory = get_session_factory()
    async with factory() as db_session:
        order_svc = OrderService(db_session)

        items = [
            OrderItem(
                sku=item["sku"],
                name=item["name"],
                quantity=item.get("quantity", 1),
                image_url=item.get("image_url", ""),
            )
            for item in order_data.get("items", [])
        ]

        order_create = OrderCreate(
            warehouse_id=order_data.get("warehouse_id", 1),
            platform_order_id=order_data.get("platform_order_id", "SIM001"),
            platform="simulation",
            rider_phone="13800000000",
            items=items,
        )
        await order_svc.create_order(order_create)

        # Run the agent
        agent = AgentBrain(
            config=config.agent,
            call=call,
            camera=camera,
            vision=vision,
            order_service=order_svc,
            warehouse_id=order_data.get("warehouse_id", 1),
            warehouse_name=order_data.get("warehouse_name", "测试仓库"),
        )

        summary = await agent.handle_call()

    # Cleanup
    await camera.disconnect()
    await vision.close()
    await close_db()

    # Print results
    logger.info("=" * 60)
    logger.info("SIMULATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Final state: {summary['final_state']}")
    logger.info(f"Items confirmed: {summary['items_confirmed']}/{summary['items_total']}")
    logger.info(f"Total corrections: {summary['total_corrections']}")
    logger.info(f"Escalated: {summary['escalated']}")

    logger.info("\n--- TRANSCRIPT ---")
    for entry in summary.get("transcript", []):
        role = "🤖 AI" if entry["role"] == "ai" else "🏍️ 骑手"
        logger.info(f"{role}: {entry['text']}")

    logger.info("\n--- AI SPOKEN LINES ---")
    for line in tts.spoken_lines:
        logger.info(f"  [AI说] {line}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="WatchBot Phase 0 Offline Simulation")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--order-file", required=True, help="Path to order JSON file")
    parser.add_argument("--rider-script", help="Path to rider script JSON (list of strings)")
    args = parser.parse_args()

    # Load order data
    order_path = Path(args.order_file)
    if not order_path.exists():
        logger.error(f"Order file not found: {order_path}")
        sys.exit(1)

    with open(order_path) as f:
        order_data = json.load(f)

    # Load rider script if provided
    rider_script = None
    if args.rider_script:
        with open(args.rider_script) as f:
            rider_script = json.load(f)

    # Run
    summary = asyncio.run(run_simulation(args.video, order_data, rider_script))

    # Save results
    output_path = Path("simulation_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()

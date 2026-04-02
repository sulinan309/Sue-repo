"""Call session manager: handles concurrent phone calls via WebSocket.

Each incoming call creates a CallSession that coordinates ASR/TTS
with the Agent brain.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable, Optional

from loguru import logger

from watchbot.telephony.asr import ASRClient, SimulatedASR
from watchbot.telephony.tts import TTSClient, SimulatedTTS


class CallSession:
    """Represents a single active phone call."""

    def __init__(
        self,
        call_id: str,
        caller_phone: str,
        asr: ASRClient | SimulatedASR,
        tts: TTSClient | SimulatedTTS,
    ):
        self.call_id = call_id
        self.caller_phone = caller_phone
        self.asr = asr
        self.tts = tts
        self.started_at = datetime.now()
        self.ended_at: Optional[datetime] = None
        self.active = True
        self.transcript: list[dict] = []

    async def speak(self, text: str) -> None:
        """Send TTS response to the rider."""
        if not self.active:
            return
        self.transcript.append({"role": "ai", "text": text, "time": datetime.now().isoformat()})
        await self.tts.synthesize(text)

    async def listen(self, audio_bytes: bytes = b"") -> str:
        """Wait for rider's speech and return recognized text."""
        if not self.active:
            return ""
        text = await self.asr.recognize_once(audio_bytes)
        if text:
            self.transcript.append(
                {"role": "rider", "text": text, "time": datetime.now().isoformat()}
            )
        return text

    def end(self) -> None:
        """Mark the call as ended."""
        self.active = False
        self.ended_at = datetime.now()


class CallManager:
    """Manages multiple concurrent call sessions."""

    def __init__(self):
        self._sessions: dict[str, CallSession] = {}

    def create_session(
        self,
        call_id: str,
        caller_phone: str,
        asr: ASRClient | SimulatedASR,
        tts: TTSClient | SimulatedTTS,
    ) -> CallSession:
        """Create and register a new call session."""
        session = CallSession(call_id, caller_phone, asr, tts)
        self._sessions[call_id] = session
        logger.info(f"Call session created: {call_id} from {caller_phone}")
        return session

    def get_session(self, call_id: str) -> Optional[CallSession]:
        return self._sessions.get(call_id)

    def end_session(self, call_id: str) -> Optional[CallSession]:
        session = self._sessions.pop(call_id, None)
        if session:
            session.end()
            logger.info(f"Call session ended: {call_id}")
        return session

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    def list_active(self) -> list[str]:
        return list(self._sessions.keys())

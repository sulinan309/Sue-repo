"""TTS (Text-to-Speech) client.

Wraps the Volcengine TTS service for generating "sweet sister" voice audio.
"""

from __future__ import annotations

import base64
from typing import Optional

import httpx
from loguru import logger

from watchbot.config import TelephonyConfig


class TTSClient:
    """TTS client for Volcengine Doubao speech synthesis."""

    def __init__(self, config: TelephonyConfig):
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech audio.

        Args:
            text: Chinese text to synthesize.

        Returns:
            PCM16 audio bytes.
        """
        client = await self._ensure_client()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.tts_api_key}",
        }

        payload = {
            "app": {"appid": self._config.asr_app_id},
            "user": {"uid": "watchbot"},
            "audio": {
                "encoding": "pcm",
                "sample_rate": 16000,
                "voice_type": self._config.tts_voice_type,
                "speed_ratio": 1.0,
            },
            "request": {
                "text": text,
                "operation": "query",
            },
        }

        try:
            resp = await client.post(
                self._config.tts_endpoint,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()
            audio_b64 = result.get("data", "")
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
                logger.debug(f"TTS synthesized {len(audio_bytes)} bytes for: {text[:30]}...")
                return audio_bytes
            return b""
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return b""

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class SimulatedTTS:
    """Simulated TTS for offline testing. Logs speech output instead of generating audio."""

    def __init__(self):
        self.spoken_lines: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        """Record the text instead of generating audio."""
        logger.info(f"[AI说] {text}")
        self.spoken_lines.append(text)
        return b""

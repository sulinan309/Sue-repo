"""ASR (Automatic Speech Recognition) client.

Wraps the Volcengine streaming ASR service.
Provides both streaming and one-shot recognition modes.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, Callable, Optional

import httpx
from loguru import logger

from watchbot.config import TelephonyConfig


class ASRClient:
    """Streaming ASR client for Volcengine Doubao speech recognition."""

    def __init__(self, config: TelephonyConfig):
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def recognize_once(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """One-shot recognition of an audio clip.

        Args:
            audio_bytes: PCM16 audio data.
            sample_rate: Audio sample rate in Hz.

        Returns:
            Recognized text string.
        """
        client = await self._ensure_client()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.asr_api_key}",
        }

        import base64

        payload = {
            "app": {"appid": self._config.asr_app_id},
            "user": {"uid": "watchbot"},
            "audio": {
                "format": "pcm",
                "sample_rate": sample_rate,
                "channel": 1,
                "bits": 16,
            },
            "request": {
                "model_type": "bigmodel",
                "result_type": "single",
            },
            "data": base64.b64encode(audio_bytes).decode("utf-8"),
        }

        try:
            resp = await client.post(
                self._config.asr_endpoint,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()
            text = result.get("result", {}).get("text", "")
            logger.debug(f"ASR result: {text}")
            return text
        except Exception as e:
            logger.error(f"ASR recognize_once failed: {e}")
            return ""

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class SimulatedASR:
    """Simulated ASR for offline testing. Returns pre-scripted rider responses."""

    def __init__(self, script: list[str] | None = None):
        self._script = list(script or [])
        self._index = 0

    async def recognize_once(self, audio_bytes: bytes = b"", **kwargs) -> str:
        """Return next scripted line."""
        if self._index < len(self._script):
            text = self._script[self._index]
            self._index += 1
            logger.debug(f"SimulatedASR: {text}")
            return text
        return ""

    def reset(self) -> None:
        self._index = 0

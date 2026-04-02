"""Camera management: RTSP stream connection and frame capture.

Supports both live RTSP streams and local video files for offline testing.
"""

from __future__ import annotations

import asyncio
import base64
import io
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from watchbot.config import VisionConfig


class CaptureMode(str, Enum):
    IDLE = "idle"          # 1 frame / 10s
    NORMAL = "normal"      # 1 frame / s
    BURST = "burst"        # 3 frames / s


class CameraManager:
    """Manages video stream connection and frame capture."""

    def __init__(self, config: VisionConfig):
        self._config = config
        self._capture: Optional[cv2.VideoCapture] = None
        self._source: str = ""
        self._mode: CaptureMode = CaptureMode.IDLE
        self._connected: bool = False
        self._last_frame_time: float = 0.0

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def mode(self) -> CaptureMode:
        return self._mode

    def set_mode(self, mode: CaptureMode) -> None:
        """Switch capture frequency mode."""
        if mode != self._mode:
            logger.info(f"Camera mode: {self._mode.value} -> {mode.value}")
            self._mode = mode

    async def connect(self, source: str) -> bool:
        """Connect to an RTSP stream or local video file.

        Args:
            source: RTSP URL (rtsp://...) or local file path.
        """
        self._source = source
        logger.info(f"Connecting to video source: {source}")

        loop = asyncio.get_event_loop()
        self._capture = await loop.run_in_executor(
            None, self._open_capture, source
        )

        if self._capture and self._capture.isOpened():
            self._connected = True
            logger.info("Camera connected successfully")
            return True

        self._connected = False
        logger.warning(f"Failed to connect to camera: {source}")
        return False

    def _open_capture(self, source: str) -> Optional[cv2.VideoCapture]:
        """Open a video capture (runs in thread pool)."""
        try:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                return cap
        except Exception as e:
            logger.error(f"Error opening capture: {e}")
        return None

    async def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from the video source.

        Returns:
            BGR numpy array or None if capture failed.
        """
        if not self._connected or not self._capture:
            return None

        loop = asyncio.get_event_loop()
        ret, frame = await loop.run_in_executor(None, self._capture.read)

        if ret and frame is not None:
            self._last_frame_time = time.time()
            return frame

        logger.warning("Frame capture failed")
        return None

    async def capture_frame_as_jpeg(self, quality: Optional[int] = None) -> Optional[bytes]:
        """Capture a frame and encode as JPEG bytes."""
        frame = await self.capture_frame()
        if frame is None:
            return None

        q = quality or self._config.frame_jpeg_quality
        return self._encode_jpeg(frame, q)

    async def capture_frame_as_base64(self, quality: Optional[int] = None) -> Optional[str]:
        """Capture a frame and return as base64-encoded JPEG string."""
        jpeg_bytes = await self.capture_frame_as_jpeg(quality)
        if jpeg_bytes is None:
            return None
        return base64.b64encode(jpeg_bytes).decode("utf-8")

    def _encode_jpeg(self, frame: np.ndarray, quality: int) -> bytes:
        """Encode BGR frame to JPEG bytes, resizing if needed."""
        h, w = frame.shape[:2]
        max_w = self._config.frame_max_width
        if w > max_w:
            scale = max_w / w
            frame = cv2.resize(frame, (max_w, int(h * scale)))

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok:
            return buf.tobytes()
        return b""

    def _get_interval(self) -> float:
        """Return capture interval in seconds based on current mode."""
        if self._mode == CaptureMode.BURST:
            return 1.0 / self._config.burst_fps
        elif self._mode == CaptureMode.NORMAL:
            return 1.0 / self._config.default_fps
        else:
            return 1.0 / self._config.idle_fps

    async def should_capture_now(self) -> bool:
        """Check if enough time has elapsed for the next capture."""
        interval = self._get_interval()
        return (time.time() - self._last_frame_time) >= interval

    async def disconnect(self) -> None:
        """Release the video capture."""
        if self._capture:
            self._capture.release()
            self._capture = None
        self._connected = False
        logger.info("Camera disconnected")


async def load_image_as_base64(path: str | Path, max_width: int = 1280) -> str:
    """Load a local image file and return base64-encoded JPEG."""
    loop = asyncio.get_event_loop()

    def _load():
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w > max_width:
            scale = max_width / w
            img = img.resize((max_width, int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    return await loop.run_in_executor(None, _load)

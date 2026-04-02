"""Configuration management for WatchBot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class VisionConfig:
    """Vision model and camera configuration."""

    # Volcengine / Doubao vision model
    api_key: str = field(default_factory=lambda: os.getenv("VISION_API_KEY", ""))
    api_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "VISION_API_ENDPOINT", "https://ark.cn-beijing.volces.com/api/v3"
        )
    )
    model_id: str = field(
        default_factory=lambda: os.getenv("VISION_MODEL_ID", "doubao-vision-pro-32k")
    )

    # Frame capture settings
    default_fps: float = 1.0  # Normal: 1 frame/sec
    burst_fps: float = 3.0  # Key moments: 3 frames/sec
    idle_fps: float = 0.1  # No call: 1 frame/10sec
    frame_jpeg_quality: int = 80
    frame_max_width: int = 1280


@dataclass
class TelephonyConfig:
    """Telephony / voice configuration."""

    # Volcengine ASR
    asr_api_key: str = field(default_factory=lambda: os.getenv("ASR_API_KEY", ""))
    asr_endpoint: str = field(
        default_factory=lambda: os.getenv("ASR_ENDPOINT", "")
    )
    asr_app_id: str = field(default_factory=lambda: os.getenv("ASR_APP_ID", ""))

    # Volcengine TTS
    tts_api_key: str = field(default_factory=lambda: os.getenv("TTS_API_KEY", ""))
    tts_endpoint: str = field(
        default_factory=lambda: os.getenv("TTS_ENDPOINT", "")
    )
    tts_voice_type: str = field(
        default_factory=lambda: os.getenv("TTS_VOICE_TYPE", "zh_female_sweet")
    )

    # SIP / Call center
    sip_server: str = field(default_factory=lambda: os.getenv("SIP_SERVER", ""))
    sip_username: str = field(default_factory=lambda: os.getenv("SIP_USERNAME", ""))
    sip_password: str = field(default_factory=lambda: os.getenv("SIP_PASSWORD", ""))

    # Timing thresholds (ms)
    asr_first_word_timeout: int = 300
    tts_first_word_timeout: int = 500


@dataclass
class AgentConfig:
    """Agent brain configuration."""

    # State timeouts (seconds)
    state_idle_timeout: int = 60
    state_max_timeout: int = 180
    max_correction_attempts: int = 3
    vision_confidence_threshold: float = 0.7

    # Escalation
    escalate_after_corrections: int = 3
    escalate_after_timeout: int = 180


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./watchbot.db"
        )
    )


@dataclass
class AppConfig:
    """Top-level application configuration."""

    vision: VisionConfig = field(default_factory=VisionConfig)
    telephony: TelephonyConfig = field(default_factory=TelephonyConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true"
    )

    # Data directories
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", "./data"))
    )


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig()

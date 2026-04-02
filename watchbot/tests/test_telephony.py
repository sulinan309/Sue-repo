"""Tests for telephony components."""

from __future__ import annotations

import pytest

from watchbot.telephony.asr import SimulatedASR
from watchbot.telephony.tts import SimulatedTTS
from watchbot.telephony.call_manager import CallManager, CallSession


class TestSimulatedASR:

    @pytest.mark.asyncio
    async def test_returns_scripted_lines(self):
        asr = SimulatedASR(["取2058号", "好的", "对"])
        assert await asr.recognize_once() == "取2058号"
        assert await asr.recognize_once() == "好的"
        assert await asr.recognize_once() == "对"

    @pytest.mark.asyncio
    async def test_returns_empty_when_exhausted(self):
        asr = SimulatedASR(["一句话"])
        await asr.recognize_once()
        assert await asr.recognize_once() == ""

    @pytest.mark.asyncio
    async def test_reset(self):
        asr = SimulatedASR(["第一句"])
        await asr.recognize_once()
        asr.reset()
        assert await asr.recognize_once() == "第一句"


class TestSimulatedTTS:

    @pytest.mark.asyncio
    async def test_records_spoken_lines(self):
        tts = SimulatedTTS()
        await tts.synthesize("你好")
        await tts.synthesize("拿牛奶")
        assert tts.spoken_lines == ["你好", "拿牛奶"]


class TestCallManager:

    def test_create_and_get_session(self):
        mgr = CallManager()
        asr = SimulatedASR()
        tts = SimulatedTTS()
        session = mgr.create_session("call-1", "13800000000", asr, tts)
        assert mgr.active_count == 1
        assert mgr.get_session("call-1") is session

    def test_end_session(self):
        mgr = CallManager()
        asr = SimulatedASR()
        tts = SimulatedTTS()
        mgr.create_session("call-1", "13800000000", asr, tts)
        ended = mgr.end_session("call-1")
        assert ended is not None
        assert not ended.active
        assert mgr.active_count == 0

    @pytest.mark.asyncio
    async def test_call_session_speak_and_listen(self):
        asr = SimulatedASR(["取2058号"])
        tts = SimulatedTTS()
        session = CallSession("c1", "138", asr, tts)

        await session.speak("你好")
        text = await session.listen()

        assert text == "取2058号"
        assert len(session.transcript) == 2
        assert session.transcript[0]["role"] == "ai"
        assert session.transcript[1]["role"] == "rider"

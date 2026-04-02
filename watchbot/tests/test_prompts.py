"""Tests for the prompt/conversation generation."""

from __future__ import annotations

from watchbot.core import prompts
from watchbot.core.schemas import PickingStep


class TestPrompts:

    def test_greeting(self):
        text = prompts.greeting()
        assert "订单号" in text

    def test_order_confirmed_single(self):
        text = prompts.order_confirmed(1)
        assert "一件" in text

    def test_order_confirmed_multiple(self):
        text = prompts.order_confirmed(3)
        assert "3件" in text

    def test_guide_to_item(self):
        step = PickingStep(
            order_index=0,
            sku="YL-CM-250ML-24",
            name="伊利纯牛奶",
            shelf_id="A3",
            shelf_layer=2,
            direction="进门左转",
            appearance="蓝色包装",
            quantity=1,
        )
        text = prompts.guide_to_item(step)
        assert "A3" in text
        assert "第2层" in text
        assert "蓝色包装" in text

    def test_item_wrong_gentle_no_negative_words(self):
        step = PickingStep(
            order_index=0, sku="X", name="牛奶", shelf_id="A1",
            shelf_layer=1, direction="", appearance="蓝色包装",
        )
        text = prompts.item_wrong_gentle(step)
        assert "错" not in text
        assert "不太对" in text

    def test_hurry_response_last_item(self):
        text = prompts.hurry_response(1)
        assert "最后一件" in text

    def test_all_done(self):
        text = prompts.all_done()
        assert "齐" in text

    def test_camera_unavailable(self):
        text = prompts.camera_unavailable()
        assert "看不到" in text


class TestSystemPrompt:

    def test_build_system_prompt(self):
        prompt = prompts.build_system_prompt(
            warehouse_name="测试仓",
            order_id="2058",
            items_summary="牛奶x1, 纸巾x1",
            shelf_map="A3: 进门左转",
            camera_status="在线",
        )
        assert "测试仓" in prompt
        assert "2058" in prompt
        assert "永远不说" in prompt

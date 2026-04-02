"""Tests for the order service layer."""

from __future__ import annotations

import pytest

from watchbot.order.service import OrderService


class TestExtractOrderId:
    """Test order ID extraction from rider speech."""

    def test_plain_digits(self):
        assert OrderService._extract_order_id("2058") == "2058"

    def test_digits_with_hao(self):
        assert OrderService._extract_order_id("2058号") == "2058"

    def test_qu_order(self):
        assert OrderService._extract_order_id("取2058号") == "2058"

    def test_dingdan_prefix(self):
        assert OrderService._extract_order_id("订单号是2058") == "2058"

    def test_chinese_numbers(self):
        result = OrderService._extract_order_id("取两零五八")
        assert result == "2058"

    def test_mixed_speech(self):
        assert OrderService._extract_order_id("我来取一下2058号订单") == "2058"

    def test_no_order_id(self):
        assert OrderService._extract_order_id("你好") is None

    def test_short_number_ignored(self):
        assert OrderService._extract_order_id("12") is None

    def test_long_order_id(self):
        assert OrderService._extract_order_id("MT20240301001") == "20240301001"

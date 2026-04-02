"""Tests for the vision analyzer JSON parsing."""

from __future__ import annotations

from watchbot.vision.analyzer import VisionAnalyzer


class TestExtractJson:

    def test_plain_json(self):
        text = '{"correct": true, "confidence": 0.9}'
        result = VisionAnalyzer._extract_json(text)
        assert '"correct": true' in result

    def test_markdown_fenced(self):
        text = '```json\n{"correct": false}\n```'
        result = VisionAnalyzer._extract_json(text)
        assert '"correct": false' in result

    def test_json_with_prefix_text(self):
        text = '根据图片分析：\n{"correct": true, "confidence": 0.85, "description": "看到蓝色包装"}'
        result = VisionAnalyzer._extract_json(text)
        assert '"correct": true' in result

    def test_generic_code_fence(self):
        text = '```\n{"uncertain": true}\n```'
        result = VisionAnalyzer._extract_json(text)
        assert '"uncertain": true' in result


class TestParseCheckResult:

    def setup_method(self):
        from watchbot.config import VisionConfig
        self.analyzer = VisionAnalyzer(VisionConfig())

    def test_correct_result(self):
        raw = '{"correct": true, "uncertain": false, "confidence": 0.92, "description": "蓝色包装牛奶"}'
        result = self.analyzer._parse_check_result(raw)
        assert result.correct is True
        assert result.wrong is False
        assert result.confidence == 0.92

    def test_wrong_result(self):
        raw = '{"correct": false, "uncertain": false, "confidence": 0.88, "description": "拿的是绿色包装"}'
        result = self.analyzer._parse_check_result(raw)
        assert result.correct is False
        assert result.wrong is True
        assert result.confidence == 0.88

    def test_uncertain_result(self):
        raw = '{"correct": false, "uncertain": true, "confidence": 0.3, "description": "看不清"}'
        result = self.analyzer._parse_check_result(raw)
        assert result.uncertain is True
        assert result.wrong is False

    def test_invalid_json_returns_uncertain(self):
        result = self.analyzer._parse_check_result("这不是JSON")
        assert result.uncertain is True
        assert result.confidence == 0.0

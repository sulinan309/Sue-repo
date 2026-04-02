"""Vision analysis: call Doubao 2.0 vision model to understand warehouse frames.

Responsibilities:
- Check if rider picked the correct product
- Identify rider position and movement
- Detect anomalies in the warehouse
"""

from __future__ import annotations

import json
from typing import Optional

import httpx
from loguru import logger

from watchbot.config import VisionConfig
from watchbot.core.schemas import VisionCheckResult


# ---------------------------------------------------------------------------
# Prompt templates for vision model
# ---------------------------------------------------------------------------

PRODUCT_CHECK_PROMPT = """\
你是一个前置仓值守AI，正在通过摄像头确认骑手是否拿到了正确的商品。

当前需要拿的商品信息：
- 商品名称：{product_name}
- 外观描述：{product_appearance}
- 货架位置：{shelf_id} 第{shelf_layer}层

请观察图片中的场景，判断：
1. 骑手手中/正在拿的商品是否与目标商品匹配？
2. 如果不匹配，描述骑手实际拿的是什么。

请以JSON格式回答：
{{"correct": true/false, "uncertain": true/false, "confidence": 0.0-1.0, "description": "简短描述你看到的情况"}}

注意：
- 如果看不清楚，设 uncertain=true, confidence < 0.5
- 如果能确认是正确商品，设 correct=true, confidence > 0.7
- 如果能确认是错误商品，设 correct=false, confidence > 0.7
"""

RIDER_POSITION_PROMPT = """\
你是一个前置仓值守AI，正在通过摄像头观察仓库内的情况。

仓库布局：
{shelf_map_description}

请观察图片，回答：
1. 画面中有几个人？
2. 他们分别在仓库的什么位置？（用货架编号描述）
3. 他们正在做什么？（站立、走动、拿取商品等）

请以JSON格式回答：
{{"people_count": N, "people": [{{"position": "位置描述", "action": "动作描述"}}], "description": "整体场景描述"}}
"""

ANOMALY_DETECTION_PROMPT = """\
你是一个前置仓值守AI，正在通过摄像头监控仓库安全。

请观察图片，检查是否有以下异常情况：
1. 有人在未经授权的区域
2. 商品散落在地上
3. 货架倾倒或损坏
4. 其他异常

请以JSON格式回答：
{{"has_anomaly": true/false, "anomaly_type": "类型", "description": "描述", "severity": "low/medium/high"}}
"""


class VisionAnalyzer:
    """Calls the vision model API to analyze warehouse frames."""

    def __init__(self, config: VisionConfig):
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _call_vision_model(
        self, image_base64: str, prompt: str, reference_image_base64: Optional[str] = None
    ) -> str:
        """Call the Doubao vision model API.

        Args:
            image_base64: Base64-encoded JPEG of the camera frame.
            prompt: Text prompt for the model.
            reference_image_base64: Optional reference product image.

        Returns:
            Raw text response from the model.
        """
        client = await self._ensure_client()

        messages_content = []
        messages_content.append({"type": "text", "text": prompt})
        messages_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
        })

        if reference_image_base64:
            messages_content.append({"type": "text", "text": "以下是目标商品的参考图片："})
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{reference_image_base64}"},
            })

        payload = {
            "model": self._config.model_id,
            "messages": [{"role": "user", "content": messages_content}],
            "max_tokens": 512,
            "temperature": 0.1,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.api_key}",
        }

        try:
            resp = await client.post(
                f"{self._config.api_endpoint}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            return ""

    async def check_product(
        self,
        frame_base64: str,
        product_name: str,
        product_appearance: str,
        shelf_id: str,
        shelf_layer: int,
        reference_image_base64: Optional[str] = None,
    ) -> VisionCheckResult:
        """Check if the rider picked the correct product.

        Returns a VisionCheckResult with correct/wrong/uncertain status.
        """
        prompt = PRODUCT_CHECK_PROMPT.format(
            product_name=product_name,
            product_appearance=product_appearance,
            shelf_id=shelf_id,
            shelf_layer=shelf_layer,
        )

        raw = await self._call_vision_model(frame_base64, prompt, reference_image_base64)

        if not raw:
            return VisionCheckResult(uncertain=True, confidence=0.0, description="视觉模型无响应")

        return self._parse_check_result(raw)

    async def detect_rider_position(
        self, frame_base64: str, shelf_map_description: str
    ) -> dict:
        """Detect rider position(s) in the warehouse frame."""
        prompt = RIDER_POSITION_PROMPT.format(shelf_map_description=shelf_map_description)
        raw = await self._call_vision_model(frame_base64, prompt)
        try:
            return json.loads(self._extract_json(raw))
        except (json.JSONDecodeError, ValueError):
            return {"people_count": 0, "people": [], "description": raw}

    async def detect_anomaly(self, frame_base64: str) -> dict:
        """Run anomaly detection on the frame."""
        raw = await self._call_vision_model(frame_base64, ANOMALY_DETECTION_PROMPT)
        try:
            return json.loads(self._extract_json(raw))
        except (json.JSONDecodeError, ValueError):
            return {"has_anomaly": False, "description": raw}

    def _parse_check_result(self, raw: str) -> VisionCheckResult:
        """Parse the vision model's JSON response into VisionCheckResult."""
        try:
            data = json.loads(self._extract_json(raw))
            correct = bool(data.get("correct", False))
            uncertain = bool(data.get("uncertain", False))
            confidence = float(data.get("confidence", 0.0))
            description = data.get("description", "")

            wrong = not correct and not uncertain and confidence > 0.5

            return VisionCheckResult(
                correct=correct,
                wrong=wrong,
                uncertain=uncertain,
                confidence=confidence,
                description=description,
                raw_response=raw,
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse vision result: {e}, raw: {raw[:200]}")
            return VisionCheckResult(
                uncertain=True, confidence=0.0, description=raw[:200], raw_response=raw
            )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON object from text that may contain markdown fences."""
        text = text.strip()
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return text[start:end].strip()
        if "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            return text[start:end].strip()
        # Try to find raw JSON
        for i, c in enumerate(text):
            if c == "{":
                depth = 0
                for j in range(i, len(text)):
                    if text[j] == "{":
                        depth += 1
                    elif text[j] == "}":
                        depth -= 1
                    if depth == 0:
                        return text[i : j + 1]
        return text

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

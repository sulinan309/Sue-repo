"""Order data service: fetch and manage orders from platforms or manual input.

Supports:
- Manual order creation via admin API
- Meituan Open Platform API (when available)
- Eleme Fengniao Open Platform API (when available)
- Order lookup by platform_order_id or rider_phone
"""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from watchbot.core.models import Order, OrderStatus, Product, Warehouse
from watchbot.core.schemas import OrderCreate, OrderItem, PickingStep


class OrderService:
    """Service layer for order operations."""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def create_order(self, data: OrderCreate) -> Order:
        """Create a new order (manual input or platform sync)."""
        order = Order(
            warehouse_id=data.warehouse_id,
            platform_order_id=data.platform_order_id,
            platform=data.platform,
            rider_phone=data.rider_phone,
            items_json=[item.model_dump() for item in data.items],
            total_items=sum(item.quantity for item in data.items),
        )
        self._db.add(order)
        await self._db.commit()
        await self._db.refresh(order)
        logger.info(f"Order created: {order.platform_order_id} with {order.total_items} items")
        return order

    async def find_by_platform_id(
        self, warehouse_id: int, platform_order_id: str
    ) -> Optional[Order]:
        """Look up an order by its platform order ID."""
        stmt = select(Order).where(
            Order.warehouse_id == warehouse_id,
            Order.platform_order_id == platform_order_id,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.IN_PROGRESS]),
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def find_by_rider_phone(
        self, warehouse_id: int, rider_phone: str
    ) -> list[Order]:
        """Find active orders for a rider in a warehouse."""
        stmt = select(Order).where(
            Order.warehouse_id == warehouse_id,
            Order.rider_phone == rider_phone,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.IN_PROGRESS]),
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def fuzzy_find_order(
        self, warehouse_id: int, spoken_text: str
    ) -> Optional[Order]:
        """Extract an order ID from rider's speech and look it up.

        Handles patterns like:
        - "2058号" -> 2058
        - "取两零五八" -> 2058
        - "订单号是2058" -> 2058
        """
        order_id = self._extract_order_id(spoken_text)
        if order_id:
            return await self.find_by_platform_id(warehouse_id, order_id)
        return None

    async def mark_in_progress(self, order_id: int) -> None:
        stmt = select(Order).where(Order.id == order_id)
        result = await self._db.execute(stmt)
        order = result.scalars().first()
        if order:
            order.status = OrderStatus.IN_PROGRESS
            await self._db.commit()

    async def mark_completed(self, order_id: int) -> None:
        stmt = select(Order).where(Order.id == order_id)
        result = await self._db.execute(stmt)
        order = result.scalars().first()
        if order:
            order.status = OrderStatus.COMPLETED
            await self._db.commit()

    async def build_picking_route(
        self, order: Order, warehouse: Warehouse
    ) -> list[PickingStep]:
        """Build an optimized picking route for the order.

        Uses the warehouse shelf map to create a route that minimizes
        walking distance (simple greedy: sort by shelf ID then layer).
        """
        items: list[dict] = order.items_json or []
        shelf_map: dict = warehouse.shelf_map_json or {}

        # Build product lookup from warehouse products
        stmt = select(Product).where(Product.warehouse_id == warehouse.id)
        result = await self._db.execute(stmt)
        products = {p.sku: p for p in result.scalars().all()}

        steps: list[PickingStep] = []
        for idx, item in enumerate(items):
            sku = item.get("sku", "")
            product = products.get(sku)

            step = PickingStep(
                order_index=idx,
                sku=sku,
                name=item.get("name", sku),
                shelf_id=product.shelf_id if product else "",
                shelf_layer=product.shelf_layer if product else 0,
                direction=product.direction if product else "",
                appearance=product.appearance if product else "",
                quantity=item.get("quantity", 1),
            )
            steps.append(step)

        # Sort by shelf_id then shelf_layer for efficient walking route
        steps.sort(key=lambda s: (s.shelf_id, s.shelf_layer))

        # Reassign order_index after sorting
        for i, step in enumerate(steps):
            step.order_index = i

        return steps

    @staticmethod
    def _extract_order_id(text: str) -> Optional[str]:
        """Extract order number from rider's spoken text."""
        # Direct digit sequences
        patterns = [
            r"(\d{3,20})",  # 3-20 digit number
            r"[取拿].*?(\d{3,10})",  # "取XXX号"
            r"订单.*?(\d{3,10})",  # "订单号XXX"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # Chinese number conversion (basic)
        cn_map = {"零": "0", "一": "1", "二": "2", "两": "2", "三": "3",
                  "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}
        converted = ""
        for ch in text:
            if ch in cn_map:
                converted += cn_map[ch]
            elif ch.isdigit():
                converted += ch

        if len(converted) >= 3:
            return converted

        return None

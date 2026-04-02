"""Seed the database with sample warehouse and product data for testing.

Usage:
    python -m watchbot.scripts.seed_data
"""

from __future__ import annotations

import asyncio

from loguru import logger

from watchbot.config import load_config
from watchbot.core.database import close_db, get_session_factory, init_db
from watchbot.core.models import Order, Product, Warehouse, WarehouseStatus


SAMPLE_WAREHOUSE = {
    "name": "望京前置仓01",
    "address": "北京市朝阳区望京SOHO T1",
    "phone_number": "4001234567",
    "camera_rtsp_url": "rtsp://192.168.1.100:554/stream1",
    "shelf_map_json": {
        "shelves": [
            {
                "id": "A1",
                "direction": "进门右手边第一个货架",
                "layers": [
                    {"layer": 1, "products": [{"sku": "YL-CM-250ML-24", "name": "伊利纯牛奶250ml×24盒", "appearance": "蓝色纸箱包装"}]},
                    {"layer": 2, "products": [{"sku": "MN-SN-250ML-12", "name": "蒙牛酸奶250ml×12盒", "appearance": "绿色纸箱包装"}]},
                    {"layer": 3, "products": [{"sku": "WH-KL-500ML", "name": "娃哈哈矿泉水500ml", "appearance": "透明塑料瓶"}]},
                ]
            },
            {
                "id": "A3",
                "direction": "进门左转第三个货架",
                "layers": [
                    {"layer": 1, "products": [{"sku": "KSF-BRF-5P", "name": "康师傅红烧牛肉面5连包", "appearance": "红色塑料包装"}]},
                    {"layer": 2, "products": [{"sku": "YL-CM-250ML-24", "name": "伊利纯牛奶250ml×24盒", "appearance": "蓝色纸箱包装"}]},
                ]
            },
            {
                "id": "B1",
                "direction": "中间过道左手边第一个货架",
                "layers": [
                    {"layer": 1, "products": [{"sku": "WD-ZJ-3P", "name": "维达纸巾3包装", "appearance": "蓝白色塑料包装"}]},
                    {"layer": 2, "products": [{"sku": "QD-XYJ", "name": "清风洗衣液1L", "appearance": "白色塑料瓶"}]},
                ]
            },
        ]
    },
}

SAMPLE_PRODUCTS = [
    {"sku": "YL-CM-250ML-24", "name": "伊利纯牛奶250ml×24盒", "shelf_id": "A3", "shelf_layer": 2, "direction": "进门左转第三个货架", "appearance": "蓝色纸箱包装", "stock": 50},
    {"sku": "MN-SN-250ML-12", "name": "蒙牛酸奶250ml×12盒", "shelf_id": "A1", "shelf_layer": 2, "direction": "进门右手边第一个货架", "appearance": "绿色纸箱包装", "stock": 30},
    {"sku": "WD-ZJ-3P", "name": "维达纸巾3包装", "shelf_id": "B1", "shelf_layer": 1, "direction": "中间过道左手边第一个货架", "appearance": "蓝白色塑料包装", "stock": 100},
    {"sku": "KSF-BRF-5P", "name": "康师傅红烧牛肉面5连包", "shelf_id": "A3", "shelf_layer": 1, "direction": "进门左转第三个货架", "appearance": "红色塑料包装", "stock": 40},
    {"sku": "WH-KL-500ML", "name": "娃哈哈矿泉水500ml", "shelf_id": "A1", "shelf_layer": 3, "direction": "进门右手边第一个货架", "appearance": "透明塑料瓶", "stock": 200},
    {"sku": "QD-XYJ", "name": "清风洗衣液1L", "shelf_id": "B1", "shelf_layer": 2, "direction": "中间过道左手边第一个货架", "appearance": "白色塑料瓶", "stock": 25},
]

SAMPLE_ORDER = {
    "platform_order_id": "2058",
    "platform": "meituan",
    "rider_phone": "13912345678",
    "items_json": [
        {"sku": "YL-CM-250ML-24", "name": "伊利纯牛奶250ml×24盒", "quantity": 1},
        {"sku": "WD-ZJ-3P", "name": "维达纸巾3包装", "quantity": 1},
    ],
    "total_items": 2,
}


async def seed():
    config = load_config()
    await init_db(config)

    factory = get_session_factory()
    async with factory() as db:
        # Create warehouse
        wh = Warehouse(
            name=SAMPLE_WAREHOUSE["name"],
            address=SAMPLE_WAREHOUSE["address"],
            phone_number=SAMPLE_WAREHOUSE["phone_number"],
            camera_rtsp_url=SAMPLE_WAREHOUSE["camera_rtsp_url"],
            shelf_map_json=SAMPLE_WAREHOUSE["shelf_map_json"],
            status=WarehouseStatus.ACTIVE,
        )
        db.add(wh)
        await db.commit()
        await db.refresh(wh)
        logger.info(f"Created warehouse: {wh.name} (id={wh.id})")

        # Create products
        for p in SAMPLE_PRODUCTS:
            product = Product(warehouse_id=wh.id, **p)
            db.add(product)
        await db.commit()
        logger.info(f"Created {len(SAMPLE_PRODUCTS)} products")

        # Create sample order
        order = Order(warehouse_id=wh.id, **SAMPLE_ORDER)
        db.add(order)
        await db.commit()
        await db.refresh(order)
        logger.info(f"Created sample order: {order.platform_order_id}")

    await close_db()
    logger.info("Seed data complete!")


if __name__ == "__main__":
    asyncio.run(seed())

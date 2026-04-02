"""Admin REST API for managing warehouses, products, and orders.

Provides CRUD endpoints for the warehouse manager to:
- Add/edit warehouses and camera configurations
- Manage SKU-to-shelf mappings
- Manually create orders
- View call session logs and statistics
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from watchbot.core.database import get_session_factory
from watchbot.core.models import Event, Order, Product, Session, Warehouse, WarehouseStatus
from watchbot.core.schemas import (
    OrderCreate,
    OrderResponse,
    ProductCreate,
    ProductResponse,
    WarehouseCreate,
    WarehouseResponse,
)

router = APIRouter(prefix="/api/v1", tags=["admin"])


async def get_db() -> AsyncSession:
    factory = get_session_factory()
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Warehouse endpoints
# ---------------------------------------------------------------------------

@router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(data: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    warehouse = Warehouse(
        name=data.name,
        address=data.address,
        phone_number=data.phone_number,
        camera_rtsp_url=data.camera_rtsp_url,
        shelf_map_json=data.shelf_map.model_dump() if data.shelf_map else {},
        status=WarehouseStatus.ACTIVE,
    )
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse).order_by(Warehouse.id))
    return list(result.scalars().all())


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    warehouse = result.scalars().first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


# ---------------------------------------------------------------------------
# Product endpoints
# ---------------------------------------------------------------------------

@router.post("/products", response_model=ProductResponse)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(
        warehouse_id=data.warehouse_id,
        sku=data.sku,
        name=data.name,
        image_url=data.image_url,
        shelf_id=data.shelf_id,
        shelf_layer=data.shelf_layer,
        direction=data.direction,
        appearance=data.appearance,
        stock=data.stock,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/warehouses/{warehouse_id}/products", response_model=list[ProductResponse])
async def list_products(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.warehouse_id == warehouse_id).order_by(Product.shelf_id, Product.shelf_layer)
    )
    return list(result.scalars().all())


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Order endpoints
# ---------------------------------------------------------------------------

@router.post("/orders", response_model=OrderResponse)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    from watchbot.order.service import OrderService
    svc = OrderService(db)
    order = await svc.create_order(data)
    return order


@router.get("/warehouses/{warehouse_id}/orders", response_model=list[OrderResponse])
async def list_orders(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.warehouse_id == warehouse_id).order_by(Order.created_at.desc()).limit(50)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Session / Stats endpoints
# ---------------------------------------------------------------------------

@router.get("/warehouses/{warehouse_id}/sessions")
async def list_sessions(warehouse_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session)
        .where(Session.warehouse_id == warehouse_id)
        .order_by(Session.started_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "order_id": s.order_id,
            "rider_phone": s.rider_phone,
            "state": s.state.value if s.state else None,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "items_confirmed": s.items_confirmed,
            "items_corrected": s.items_corrected,
            "escalated": s.escalated,
            "duration_seconds": s.duration_seconds,
        }
        for s in sessions
    ]


@router.get("/warehouses/{warehouse_id}/stats")
async def get_stats(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    """Get aggregated statistics for a warehouse."""
    total_sessions = await db.scalar(
        select(func.count(Session.id)).where(Session.warehouse_id == warehouse_id)
    )
    completed_sessions = await db.scalar(
        select(func.count(Session.id)).where(
            Session.warehouse_id == warehouse_id,
            Session.state == "completed",
        )
    )
    escalated_sessions = await db.scalar(
        select(func.count(Session.id)).where(
            Session.warehouse_id == warehouse_id,
            Session.escalated == 1,
        )
    )
    avg_duration = await db.scalar(
        select(func.avg(Session.duration_seconds)).where(
            Session.warehouse_id == warehouse_id,
            Session.duration_seconds.isnot(None),
        )
    )

    return {
        "total_sessions": total_sessions or 0,
        "completed_sessions": completed_sessions or 0,
        "escalated_sessions": escalated_sessions or 0,
        "escalation_rate": (
            (escalated_sessions or 0) / total_sessions if total_sessions else 0
        ),
        "avg_duration_seconds": round(avg_duration, 1) if avg_duration else None,
    }

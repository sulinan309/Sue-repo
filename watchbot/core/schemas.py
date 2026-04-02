"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Warehouse
# ---------------------------------------------------------------------------

class ShelfProduct(BaseModel):
    sku: str
    name: str
    appearance: str = ""
    image_url: str = ""


class ShelfLayer(BaseModel):
    layer: int
    products: list[ShelfProduct] = []


class Shelf(BaseModel):
    id: str
    direction: str = ""
    layers: list[ShelfLayer] = []


class ShelfMap(BaseModel):
    shelves: list[Shelf] = []


class WarehouseCreate(BaseModel):
    name: str
    address: str = ""
    phone_number: str
    camera_rtsp_url: str = ""
    shelf_map: ShelfMap = Field(default_factory=ShelfMap)


class WarehouseResponse(BaseModel):
    id: int
    name: str
    address: str
    phone_number: str
    camera_rtsp_url: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductCreate(BaseModel):
    warehouse_id: int
    sku: str
    name: str
    image_url: str = ""
    shelf_id: str
    shelf_layer: int
    direction: str = ""
    appearance: str = ""
    stock: int = 0


class ProductResponse(BaseModel):
    id: int
    warehouse_id: int
    sku: str
    name: str
    shelf_id: str
    shelf_layer: int
    direction: str
    appearance: str
    stock: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------

class OrderItem(BaseModel):
    sku: str
    name: str
    quantity: int = 1
    image_url: str = ""


class OrderCreate(BaseModel):
    warehouse_id: int
    platform_order_id: str
    platform: str = "manual"
    rider_phone: str = ""
    items: list[OrderItem] = []


class OrderResponse(BaseModel):
    id: int
    warehouse_id: int
    platform_order_id: str
    platform: Optional[str]
    rider_phone: Optional[str]
    status: str
    items_json: list
    total_items: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SessionResponse(BaseModel):
    id: int
    warehouse_id: int
    order_id: Optional[int]
    rider_phone: Optional[str]
    state: str
    started_at: datetime
    ended_at: Optional[datetime]
    items_confirmed: int
    items_corrected: int
    escalated: int
    duration_seconds: Optional[float]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Vision
# ---------------------------------------------------------------------------

class VisionCheckResult(BaseModel):
    """Result from the vision model checking a product."""
    correct: bool = False
    wrong: bool = False
    uncertain: bool = False
    confidence: float = 0.0
    description: str = ""
    raw_response: str = ""


# ---------------------------------------------------------------------------
# Picking route
# ---------------------------------------------------------------------------

class PickingStep(BaseModel):
    """One step in the picking route."""
    order_index: int
    sku: str
    name: str
    shelf_id: str
    shelf_layer: int
    direction: str
    appearance: str
    quantity: int = 1
    confirmed: bool = False
    correction_count: int = 0

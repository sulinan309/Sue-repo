"""SQLAlchemy data models for WatchBot.

Entities: Warehouse, Product, Order, Session, Event
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WarehouseStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionState(str, enum.Enum):
    """Call session state machine states."""
    IDLE = "idle"
    GREETING = "greeting"
    ORDER_MATCHING = "order_matching"
    ORDER_MATCHED = "order_matched"
    GUIDING = "guiding"
    CONFIRMING = "confirming"
    CORRECTING = "correcting"
    HELPING = "helping"
    NEXT_ITEM = "next_item"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class EventType(str, enum.Enum):
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    ASR_RESULT = "asr_result"
    TTS_PLAYED = "tts_played"
    FRAME_CAPTURED = "frame_captured"
    VISION_RESULT = "vision_result"
    ORDER_MATCHED = "order_matched"
    ITEM_CONFIRMED = "item_confirmed"
    ITEM_CORRECTED = "item_corrected"
    ESCALATION = "escalation"
    STATE_CHANGE = "state_change"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Warehouse(Base):
    """A warehouse location with camera and phone number."""

    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    camera_rtsp_url = Column(String(500))
    shelf_map_json = Column(JSON, default=dict)
    status = Column(
        Enum(WarehouseStatus), default=WarehouseStatus.ACTIVE, nullable=False
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    products = relationship("Product", back_populates="warehouse", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="warehouse", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="warehouse", cascade="all, delete-orphan")


class Product(Base):
    """A product in a warehouse with shelf location."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    image_url = Column(String(500))
    shelf_id = Column(String(20), nullable=False)
    shelf_layer = Column(Integer, nullable=False)
    direction = Column(String(200))
    appearance = Column(String(200))
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    warehouse = relationship("Warehouse", back_populates="products")


class Order(Base):
    """An order from the delivery platform."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    platform_order_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(50))  # meituan / eleme
    rider_phone = Column(String(20), index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    items_json = Column(JSON, default=list)
    total_items = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    warehouse = relationship("Warehouse", back_populates="orders")
    sessions = relationship("Session", back_populates="order")


class Session(Base):
    """A phone call session between AI and a rider."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    rider_phone = Column(String(20), index=True)
    state = Column(Enum(SessionState), default=SessionState.IDLE, nullable=False)
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    transcript_json = Column(JSON, default=list)
    items_confirmed = Column(Integer, default=0)
    items_corrected = Column(Integer, default=0)
    escalated = Column(Integer, default=0)  # 0=no, 1=yes
    duration_seconds = Column(Float, nullable=True)

    warehouse = relationship("Warehouse", back_populates="sessions")
    order = relationship("Order", back_populates="sessions")
    events = relationship("Event", back_populates="session", cascade="all, delete-orphan")


class Event(Base):
    """Event log for tracking every action in a session."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False)
    payload_json = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=func.now())

    session = relationship("Session", back_populates="events")

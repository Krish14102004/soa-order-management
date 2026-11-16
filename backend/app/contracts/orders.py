from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.core.models import StrictModel


class OrderItemContract(StrictModel):
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(gt=0)


class CreateOrderRequest(StrictModel):
    items: list[OrderItemContract] = Field(min_length=1, max_length=100)


class GetOrderRequest(StrictModel):
    order_id: UUID


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class OrderResponse(StrictModel):
    order_id: UUID
    status: OrderStatus
    items: list[OrderItemContract]
    created_at: datetime


class OrderListResponse(StrictModel):
    orders: list[OrderResponse]

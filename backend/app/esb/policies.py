from dataclasses import dataclass
from typing import Type
from pydantic import BaseModel, Field

from app.contracts.catalog import (
    AvailabilityRequest,
    AvailabilityResponse,
    EmptyRequest,
    ProductContract,
    ProductListResponse,
)
from app.contracts.orders import (
    CreateOrderRequest,
    GetOrderRequest,
    OrderListResponse,
    OrderResponse,
)
from app.core.models import StrictModel


class GetProductRequest(StrictModel):
    product_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


@dataclass(frozen=True)
class OperationPolicy:
    method: str
    path: str
    request_model: Type[BaseModel]
    response_model: Type[BaseModel]


DISPATCH_POLICIES: dict[tuple[str, str], OperationPolicy] = {
    ("catalog-service", "list-products"): OperationPolicy(
        "GET",
        "/api/catalog/products",
        EmptyRequest,
        ProductListResponse,
    ),
    ("catalog-service", "get-product"): OperationPolicy(
        "GET",
        "/api/catalog/products/{product_id}",
        GetProductRequest,
        ProductContract,
    ),
    ("catalog-service", "check-availability"): OperationPolicy(
        "POST",
        "/api/catalog/availability",
        AvailabilityRequest,
        AvailabilityResponse,
    ),
    ("order-service", "create-order"): OperationPolicy(
        "POST",
        "/api/orders",
        CreateOrderRequest,
        OrderResponse,
    ),
    ("order-service", "list-orders"): OperationPolicy(
        "GET",
        "/api/orders",
        EmptyRequest,
        OrderListResponse,
    ),
    ("order-service", "get-order"): OperationPolicy(
        "GET",
        "/api/orders/{order_id}",
        GetOrderRequest,
        OrderResponse,
    ),
}


def request_path(policy: OperationPolicy, payload: BaseModel) -> str:
    values = payload.model_dump(mode="json")
    return policy.path.format(**values)


def path_is_valid(policy: OperationPolicy, path: str) -> bool:
    return policy.path == path


__all__ = [
    "DISPATCH_POLICIES",
    "OperationPolicy",
    "path_is_valid",
    "request_path",
]

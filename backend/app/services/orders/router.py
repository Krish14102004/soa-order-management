from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from app.contracts.orders import CreateOrderRequest, OrderListResponse, OrderResponse
from app.services.orders.logic import create_order
from app.services.orders.repository import OrderRepository

router = APIRouter(prefix="/api/orders", tags=["orders"])


def get_repository(request: Request) -> OrderRepository:
    return request.app.state.order_repository


async def get_http_client(request: Request) -> httpx.AsyncClient:
    headers = {"X-Correlation-ID": str(request.state.correlation_id)}
    return httpx.AsyncClient(
        timeout=request.app.state.service_timeout_seconds,
        transport=request.app.state.http_transport,
        headers=headers,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def submit_order(
    order_request: CreateOrderRequest,
    repository: Annotated[OrderRepository, Depends(get_repository)],
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    request: Request,
) -> OrderResponse:
    async with client:
        return await create_order(
            order_request,
            repository,
            client,
            request.state.correlation_id,
        )


@router.get("", response_model=OrderListResponse)
def list_orders(
    repository: Annotated[OrderRepository, Depends(get_repository)],
) -> OrderListResponse:
    return OrderListResponse(orders=repository.list_orders())


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    repository: Annotated[OrderRepository, Depends(get_repository)],
) -> OrderResponse:
    order = repository.get_order(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order was not found",
        )
    return order

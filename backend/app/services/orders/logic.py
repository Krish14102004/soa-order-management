import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.contracts.catalog import AvailabilityResponse
from app.contracts.orders import CreateOrderRequest, OrderResponse, OrderStatus
from app.core.config import CATALOG_SERVICE_URL
from app.services.orders.repository import OrderRepository

logger = logging.getLogger(__name__)


async def create_order(
    order_request: CreateOrderRequest,
    repository: OrderRepository,
    client: httpx.AsyncClient,
    correlation_id: UUID,
) -> OrderResponse:
    for item in order_request.items:
        try:
            response = await client.post(
                f"{CATALOG_SERVICE_URL}/api/catalog/availability",
                json=item.model_dump(mode="json"),
            )
            response.raise_for_status()
            availability = AvailabilityResponse.model_validate(response.json())
        except httpx.TimeoutException as exc:
            logger.warning(
                "Catalog timeout correlation_id=%s error_type=%s",
                correlation_id,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Catalog Service did not respond in time",
            ) from exc
        except httpx.RequestError as exc:
            logger.warning(
                "Catalog unavailable correlation_id=%s error_type=%s",
                correlation_id,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Catalog Service is unavailable",
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Catalog returned HTTP %s correlation_id=%s",
                exc.response.status_code,
                correlation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Catalog Service returned an unexpected response",
            ) from exc
        except (ValueError, ValidationError) as exc:
            logger.warning(
                "Catalog response invalid correlation_id=%s error_type=%s",
                correlation_id,
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Catalog Service returned an invalid response",
            ) from exc

        if not availability.available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Requested quantity is unavailable for product '{item.product_id}'",
            )

    order = OrderResponse(
        order_id=uuid4(),
        status=OrderStatus.CONFIRMED,
        items=order_request.items,
        created_at=datetime.now(timezone.utc),
    )
    return repository.create_order(order)

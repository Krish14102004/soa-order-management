from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request, status

from app.contracts.catalog import (
    AvailabilityRequest,
    AvailabilityResponse,
    ProductContract,
    ProductListResponse,
)
from app.services.catalog.repository import CatalogRepository

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def get_repository(request: Request) -> CatalogRepository:
    return request.app.state.catalog_repository


@router.get("/products", response_model=ProductListResponse)
def list_products(request: Request) -> ProductListResponse:
    products = get_repository(request).list_products()
    return ProductListResponse(products=products)


@router.get("/products/{product_id}", response_model=ProductContract)
def get_product(
    request: Request,
    product_id: Annotated[str, Path(min_length=1, max_length=80)],
) -> ProductContract:
    product = get_repository(request).get_product(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product was not found",
        )
    return product


@router.post("/availability", response_model=AvailabilityResponse)
def check_availability(
    request: Request,
    availability_request: AvailabilityRequest,
) -> AvailabilityResponse:
    available, available_quantity = get_repository(request).check_availability(
        availability_request.product_id,
        availability_request.quantity,
    )
    return AvailabilityResponse(
        product_id=availability_request.product_id,
        requested_quantity=availability_request.quantity,
        available=available,
        available_quantity=available_quantity,
    )

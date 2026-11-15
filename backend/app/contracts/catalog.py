from pydantic import Field

from app.core.models import StrictModel


class EmptyRequest(StrictModel):
    pass


class ProductContract(StrictModel):
    product_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    available_quantity: int = Field(ge=0)


class ProductListResponse(StrictModel):
    products: list[ProductContract]


class AvailabilityRequest(StrictModel):
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(gt=0)


class AvailabilityResponse(StrictModel):
    product_id: str = Field(min_length=1, max_length=80)
    requested_quantity: int = Field(gt=0)
    available: bool
    available_quantity: int = Field(ge=0)


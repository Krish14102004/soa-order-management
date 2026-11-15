from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import ConfigDict, Field

from app.core.models import StrictModel

PayloadT = TypeVar("PayloadT")


class ErrorBody(StrictModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=500)


class ErrorDetail(StrictModel):
    location: list[str | int] = Field(default_factory=list)
    message: str = Field(min_length=1, max_length=500)
    code: str = Field(min_length=1, max_length=80)


class ErrorResponse(StrictModel):
    error: ErrorBody
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: UUID | None = None


class MessageEnvelope(StrictModel, Generic[PayloadT]):
    model_config = ConfigDict(extra="forbid")

    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    service: str = Field(min_length=1, max_length=80)
    operation: str = Field(min_length=1, max_length=80)
    contract_version: str = Field(default="v1", pattern=r"^v[1-9][0-9]*$")
    payload: PayloadT

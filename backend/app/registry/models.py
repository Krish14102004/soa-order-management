from datetime import datetime, timezone
from enum import StrEnum
from ipaddress import ip_address
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, Field, field_validator, model_validator

from app.core.models import StrictModel


class ServiceHealth(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class ServiceOperation(StrictModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9-]*$", max_length=80)
    method: Literal["GET", "POST"]
    path: str = Field(pattern=r"^/[a-zA-Z0-9_./{}-]*$", max_length=200)
    contract_version: str = Field(default="v1", pattern=r"^v[1-9][0-9]*$")


class ServiceRegistration(StrictModel):
    service_name: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)
    description: str = Field(min_length=1, max_length=500)
    endpoint: AnyHttpUrl
    capabilities: list[str] = Field(min_length=1, max_length=30)
    contract_url: str = Field(min_length=1, max_length=300)
    operations: list[ServiceOperation] = Field(min_length=1, max_length=50)

    @field_validator("endpoint")
    @classmethod
    def require_local_http_endpoint(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        parsed = urlsplit(str(value))
        if (
            parsed.scheme != "http"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("endpoint must be an unauthenticated local HTTP URL")

        hostname = parsed.hostname
        is_localhost = hostname == "localhost"
        try:
            is_loopback_ip = hostname is not None and ip_address(hostname).is_loopback
        except ValueError:
            is_loopback_ip = False

        if not (is_localhost or is_loopback_ip):
            raise ValueError("endpoint host must be localhost or a loopback IP address")
        return value

    @field_validator("contract_url")
    @classmethod
    def require_local_contract_reference(cls, value: str) -> str:
        if not value.startswith("/") or value.startswith("//"):
            raise ValueError("contract_url must be a local absolute path")
        if ".." in urlsplit(value).path.split("/"):
            raise ValueError("contract_url must not contain parent-directory segments")
        return value

    @field_validator("capabilities")
    @classmethod
    def normalize_capabilities(cls, values: list[str]) -> list[str]:
        normalized = [value.strip().lower() for value in values]
        if any(not value or len(value) > 80 for value in normalized):
            raise ValueError("capabilities must be non-empty strings of at most 80 characters")
        if len(set(normalized)) != len(normalized):
            raise ValueError("capabilities must be unique")
        return normalized

    @model_validator(mode="after")
    def require_unique_operation_names(self) -> "ServiceRegistration":
        names = [operation.name for operation in self.operations]
        if len(set(names)) != len(names):
            raise ValueError("operation names must be unique within a service")
        return self


class ServiceDescriptor(ServiceRegistration):
    status: ServiceHealth = ServiceHealth.UNKNOWN
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

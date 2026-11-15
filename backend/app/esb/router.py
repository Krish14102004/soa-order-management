import logging
from time import perf_counter
from typing import Annotated, Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from app.contracts.common import ErrorBody, ErrorDetail, ErrorResponse, MessageEnvelope
from app.core.models import StrictModel
from app.esb.policies import (
    DISPATCH_POLICIES,
    path_is_valid,
    request_path,
)
from app.esb.tracing import MessageTrace, TraceStore
from app.registry.models import ServiceDescriptor
from app.registry.repository import ServiceRegistry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/esb", tags=["esb"])


class DispatchResponse(StrictModel):
    message_id: UUID
    correlation_id: UUID
    service: str
    operation: str
    status_code: int
    payload: Any


def get_registry(request: Request) -> ServiceRegistry:
    return request.app.state.service_registry


def get_trace_store(request: Request) -> TraceStore:
    return request.app.state.trace_store


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=request.app.state.service_timeout_seconds,
        transport=request.app.state.http_transport,
    )


RegistryDependency = Annotated[ServiceRegistry, Depends(get_registry)]
TraceDependency = Annotated[TraceStore, Depends(get_trace_store)]


def error_response(
    correlation_id: UUID,
    code: str,
    message: str,
    status_code: int,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    response = ErrorResponse(
        error=ErrorBody(code=code, message=message),
        details=details or [],
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
        headers={"X-Correlation-ID": str(correlation_id)},
    )


def record_trace(
    store: TraceStore,
    envelope: MessageEnvelope[dict[str, Any]],
    destination: str,
    status_text: str,
    status_code: int,
    started_at: float,
) -> None:
    store.record(
        MessageTrace(
            message_id=envelope.message_id,
            correlation_id=envelope.correlation_id,
            source="consumer",
            destination=destination,
            operation=envelope.operation,
            status=status_text,
            status_code=status_code,
            duration_ms=(perf_counter() - started_at) * 1000,
        )
    )


def resolve_operation(
    service: ServiceDescriptor,
    envelope: MessageEnvelope[dict[str, Any]],
):
    operation = next(
        (
            candidate
            for candidate in service.operations
            if candidate.name == envelope.operation
        ),
        None,
    )
    if operation is None:
        return None, None, "unknown_operation"

    policy = DISPATCH_POLICIES.get((service.service_name, operation.name))
    if policy is None:
        return operation, None, "unsupported_operation"
    if envelope.contract_version != operation.contract_version:
        return operation, None, "contract_version_mismatch"
    if not path_is_valid(policy, operation.path) or operation.method != policy.method:
        return operation, None, "contract_route_mismatch"
    return operation, policy, None


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_message(
    envelope: MessageEnvelope[dict[str, Any]],
    request: Request,
    response_metadata: Response,
    registry: RegistryDependency,
    trace_store: TraceDependency,
) -> DispatchResponse | JSONResponse:
    response_metadata.headers["X-Correlation-ID"] = str(envelope.correlation_id)
    started_at = perf_counter()
    service = registry.get_service(envelope.service)
    if service is None:
        record_trace(
            trace_store,
            envelope,
            envelope.service,
            "error",
            status.HTTP_404_NOT_FOUND,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            "unknown_service",
            "The requested service is not registered",
            status.HTTP_404_NOT_FOUND,
        )

    operation, policy, route_error = resolve_operation(service, envelope)
    if route_error is not None:
        status_code = (
            status.HTTP_501_NOT_IMPLEMENTED
            if route_error == "unsupported_operation"
            else status.HTTP_404_NOT_FOUND
            if route_error == "unknown_operation"
            else 422
        )
        code = route_error
        messages = {
            "unsupported_operation": "The gateway does not support this operation",
            "unknown_operation": "The operation is not registered for this service",
            "contract_version_mismatch": "The requested contract version is not supported",
            "contract_route_mismatch": "The registered operation does not match its contract",
        }
        record_trace(
            trace_store,
            envelope,
            service.service_name,
            "error",
            status_code,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            code,
            messages[route_error],
            status_code,
        )

    assert operation is not None and policy is not None
    try:
        validated_payload = policy.request_model.model_validate(envelope.payload)
    except ValidationError as exc:
        details = [
            ErrorDetail(
                location=["payload", *error["loc"]],
                message=error["msg"],
                code=error["type"],
            )
            for error in exc.errors()
        ]
        record_trace(
            trace_store,
            envelope,
            service.service_name,
            "error",
            422,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            "validation_error",
            "Message payload does not match the published contract",
            422,
            details,
        )

    destination = f"{service.service_name}:{operation.name}"
    url = f"{str(service.endpoint).rstrip('/')}{request_path(policy, validated_payload)}"
    try:
        async with httpx.AsyncClient(
            timeout=request.app.state.service_timeout_seconds,
            transport=request.app.state.http_transport,
        ) as client:
            response = await client.request(
                operation.method,
                url,
                json=validated_payload.model_dump(mode="json")
                if operation.method != "GET"
                else None,
                headers={"X-Correlation-ID": str(envelope.correlation_id)},
            )
    except httpx.TimeoutException:
        logger.warning(
            "Provider timeout correlation_id=%s destination=%s",
            envelope.correlation_id,
            destination,
        )
        record_trace(
            trace_store,
            envelope,
            destination,
            "error",
            status.HTTP_504_GATEWAY_TIMEOUT,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            "provider_timeout",
            "The provider did not respond in time",
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except httpx.RequestError:
        logger.exception(
            "Provider request failed correlation_id=%s destination=%s",
            envelope.correlation_id,
            destination,
        )
        record_trace(
            trace_store,
            envelope,
            destination,
            "error",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            "provider_unavailable",
            "The provider is unavailable",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception:
        logger.exception(
            "Unexpected gateway failure correlation_id=%s destination=%s",
            envelope.correlation_id,
            destination,
        )
        record_trace(
            trace_store,
            envelope,
            destination,
            "error",
            status.HTTP_502_BAD_GATEWAY,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            "gateway_error",
            "The gateway could not complete the request",
            status.HTTP_502_BAD_GATEWAY,
        )

    if response.status_code >= 400:
        try:
            provider_payload = response.json()
            provider_error = provider_payload.get("error")
            if not isinstance(provider_error, dict):
                provider_error = {}
        except ValueError:
            provider_error = {}
        provider_code = provider_error.get("code")
        provider_message = provider_error.get("message")
        if not isinstance(provider_code, str) or not provider_code:
            provider_code = "provider_error"
        if not isinstance(provider_message, str) or not provider_message:
            provider_message = "The provider could not complete the request"
        record_trace(
            trace_store,
            envelope,
            destination,
            "error",
            response.status_code,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            provider_code[:80],
            provider_message[:500],
            response.status_code,
        )

    try:
        payload = policy.response_model.model_validate(response.json()).model_dump(
            mode="json"
        )
    except (ValueError, ValidationError):
        logger.error(
            "Provider returned non-JSON response correlation_id=%s destination=%s",
            envelope.correlation_id,
            destination,
        )
        record_trace(
            trace_store,
            envelope,
            destination,
            "error",
            status.HTTP_502_BAD_GATEWAY,
            started_at,
        )
        return error_response(
            envelope.correlation_id,
            "invalid_provider_response",
            "The provider returned an invalid response",
            status.HTTP_502_BAD_GATEWAY,
        )

    record_trace(
        trace_store,
        envelope,
        destination,
        "success",
        response.status_code,
        started_at,
    )
    return DispatchResponse(
        message_id=envelope.message_id,
        correlation_id=envelope.correlation_id,
        service=envelope.service,
        operation=envelope.operation,
        status_code=response.status_code,
        payload=payload,
    )


@router.get("/traces", response_model=list[MessageTrace])
def list_recent_traces(
    trace_store: TraceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[MessageTrace]:
    return trace_store.recent(limit)

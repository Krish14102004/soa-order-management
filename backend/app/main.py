"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.contracts.common import ErrorBody, ErrorDetail, ErrorResponse
from app.core.config import (
    CATALOG_SERVICE_URL,
    DATABASE_PATH,
    ESB_TIMEOUT_SECONDS,
    ORDER_SERVICE_URL,
)
from app.esb.router import router as esb_router
from app.esb.tracing import TraceStore
from app.registry.repository import ServiceRegistry
from app.registry.router import router as registry_router
from app.registry.models import ServiceOperation, ServiceRegistration
from app.services.catalog.repository import CatalogRepository
from app.services.catalog.router import router as catalog_router
from app.services.orders.repository import OrderRepository
from app.services.orders.router import router as orders_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    database_path = application.state.database_path
    catalog_repository = CatalogRepository(database_path)
    order_repository = OrderRepository(database_path)
    catalog_repository.initialize()
    order_repository.initialize()

    registry = ServiceRegistry()
    registry.register(
        ServiceRegistration(
            service_name="catalog-service",
            description="Product catalogue and availability provider",
            endpoint=CATALOG_SERVICE_URL,
            capabilities=["catalog", "availability"],
            contract_url="/openapi.json",
            operations=[
                ServiceOperation(
                    name="list-products",
                    method="GET",
                    path="/api/catalog/products",
                ),
                ServiceOperation(
                    name="get-product",
                    method="GET",
                    path="/api/catalog/products/{product_id}",
                ),
                ServiceOperation(
                    name="check-availability",
                    method="POST",
                    path="/api/catalog/availability",
                ),
            ],
        )
    )
    registry.register(
        ServiceRegistration(
            service_name="order-service",
            description="Order creation and status provider",
            endpoint=ORDER_SERVICE_URL,
            capabilities=["orders"],
            contract_url="/openapi.json",
            operations=[
                ServiceOperation(
                    name="create-order",
                    method="POST",
                    path="/api/orders",
                ),
                ServiceOperation(
                    name="get-order",
                    method="GET",
                    path="/api/orders/{order_id}",
                ),
            ],
        )
    )

    application.state.catalog_repository = catalog_repository
    application.state.order_repository = order_repository
    application.state.service_registry = registry
    application.state.trace_store = TraceStore()
    yield

app = FastAPI(
    title="SOA Order Management API",
    description="Educational SOA demonstration API",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.database_path = DATABASE_PATH
app.state.service_timeout_seconds = ESB_TIMEOUT_SECONDS
app.state.http_transport = None
app.include_router(registry_router)
app.include_router(catalog_router)
app.include_router(orders_router)
app.include_router(esb_router)

# Local development CORS; restrict origins further before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Correlation-ID"],
)


@app.middleware("http")
async def correlate_request(request: Request, call_next):
    provided_id = request.headers.get("X-Correlation-ID")
    try:
        request.state.correlation_id = UUID(provided_id) if provided_id else uuid4()
    except ValueError:
        request.state.correlation_id = uuid4()
    response = await call_next(request)
    if "X-Correlation-ID" not in response.headers:
        response.headers["X-Correlation-ID"] = str(request.state.correlation_id)
    return response


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Verify that the backend process is responding."""
    return {"status": "ok", "service": "soa-order-management-api"}


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = {
        400: "bad_request",
        404: "not_found",
        409: "conflict",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "upstream_timeout",
    }.get(exc.status_code, "request_error")
    message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed"
    if len(message) > 500:
        message = "The request could not be completed"
    correlation_id = getattr(request.state, "correlation_id", None)
    response = ErrorResponse(
        error=ErrorBody(code=code, message=message),
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
        headers={**(exc.headers or {}), **(
            {"X-Correlation-ID": str(correlation_id)} if correlation_id else {}
        )},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = [
        ErrorDetail(
            location=[part if isinstance(part, (str, int)) else str(part) for part in error["loc"]],
            message=error["msg"],
            code=error["type"],
        )
        for error in exc.errors()
    ]
    response = ErrorResponse(
        error=ErrorBody(
            code="validation_error",
            message="Request validation failed",
        ),
        details=details,
        correlation_id=getattr(request.state, "correlation_id", None),
    )
    return JSONResponse(
        status_code=422,
        content=response.model_dump(mode="json"),
    )

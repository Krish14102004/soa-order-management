from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.registry.models import ServiceOperation, ServiceRegistration
from app.registry.repository import ServiceRegistry


@pytest.fixture
def client(tmp_path):
    original_database_path = app.state.database_path
    original_transport = app.state.http_transport
    app.state.database_path = str(tmp_path / "esb-tests.sqlite3")
    app.state.http_transport = httpx.ASGITransport(app=app)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.database_path = original_database_path
        app.state.http_transport = original_transport


def envelope(
    service: str = "order-service",
    operation: str = "create-order",
    payload: dict | None = None,
) -> dict:
    return {
        "message_id": "11111111-1111-4111-8111-111111111111",
        "correlation_id": "22222222-2222-4222-8222-222222222222",
        "service": service,
        "operation": operation,
        "contract_version": "v1",
        "payload": (
            payload
            if payload is not None
            else {"items": [{"product_id": "book-soa-101", "quantity": 2}]}
        ),
    }


def test_gateway_dispatches_order_and_records_correlation_trace(client: TestClient):
    response = client.post("/api/esb/dispatch", json=envelope())

    assert response.status_code == 200
    result = response.json()
    assert result["status_code"] == 201
    assert result["payload"]["status"] == "confirmed"
    assert result["correlation_id"] == "22222222-2222-4222-8222-222222222222"
    assert response.headers["X-Correlation-ID"] == result["correlation_id"]

    traces = client.get("/api/esb/traces").json()
    assert len(traces) == 1
    assert traces[0]["correlation_id"] == result["correlation_id"]
    assert traces[0]["destination"] == "order-service:create-order"
    assert traces[0]["status"] == "success"


def test_gateway_rejects_payload_that_does_not_match_contract(client: TestClient):
    payload = envelope(payload={"items": [{"product_id": "book-soa-101", "quantity": 0}]})

    response = client.post("/api/esb/dispatch", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["details"]
    assert client.get("/api/esb/traces").json()[0]["status"] == "error"


def test_gateway_returns_structured_errors_for_unknown_service_and_operation(
    client: TestClient,
):
    unknown_service = client.post(
        "/api/esb/dispatch",
        json=envelope(service="missing-service"),
    )
    unknown_operation = client.post(
        "/api/esb/dispatch",
        json=envelope(operation="cancel-order"),
    )

    assert unknown_service.status_code == 404
    assert unknown_service.json()["error"]["code"] == "unknown_service"
    assert unknown_operation.status_code == 404
    assert unknown_operation.json()["error"]["code"] == "unknown_operation"


def test_gateway_reports_unavailable_provider(client: TestClient):
    app.state.service_registry = ServiceRegistry()
    app.state.service_registry.register(
        ServiceRegistration(
            service_name="order-service",
            description="Order provider used by this test",
            endpoint="http://127.0.0.1:1",
            capabilities=["orders"],
            contract_url="/openapi.json",
            operations=[
                ServiceOperation(
                    name="create-order",
                    method="POST",
                    path="/api/orders",
                )
            ],
        )
    )
    async def unavailable_provider(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Provider is offline", request=request)

    app.state.http_transport = httpx.MockTransport(unavailable_provider)

    response = client.post("/api/esb/dispatch", json=envelope())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"
    assert client.get("/api/esb/traces").json()[0]["status"] == "error"


def test_gateway_rejects_invalid_contract_version(client: TestClient):
    payload = envelope()
    payload["contract_version"] = "v2"

    response = client.post("/api/esb/dispatch", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "contract_version_mismatch"


def test_gateway_dispatches_catalog_get_operation(client: TestClient):
    response = client.post(
        "/api/esb/dispatch",
        json=envelope(
            service="catalog-service",
            operation="list-products",
            payload={},
        ),
    )

    assert response.status_code == 200
    assert response.json()["status_code"] == 200
    assert len(response.json()["payload"]["products"]) == 3


def test_gateway_normalizes_provider_timeout(client: TestClient):
    async def timed_out_provider(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Provider timed out", request=request)

    app.state.http_transport = httpx.MockTransport(timed_out_provider)

    response = client.post("/api/esb/dispatch", json=envelope())

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "provider_timeout"


def test_gateway_propagates_provider_business_error(client: TestClient):
    response = client.post(
        "/api/esb/dispatch",
        json=envelope(payload={
            "items": [{"product_id": "book-soa-101", "quantity": 1000}]
        }),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert "unavailable" in response.json()["error"]["message"]


def test_invalid_correlation_id_is_replaced_with_a_valid_id(client: TestClient):
    response = client.post(
        "/api/esb/dispatch",
        headers={"X-Correlation-ID": "not-a-uuid"},
        json=envelope(),
    )

    assert response.status_code == 200
    assert UUID(response.headers["X-Correlation-ID"])

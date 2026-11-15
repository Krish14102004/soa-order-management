import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path):
    original_database_path = app.state.database_path
    original_transport = app.state.http_transport
    app.state.database_path = str(tmp_path / "provider-tests.sqlite3")
    app.state.http_transport = httpx.ASGITransport(app=app)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.database_path = original_database_path
        app.state.http_transport = original_transport


def test_providers_publish_service_descriptions(client: TestClient):
    response = client.get("/api/registry/services")

    assert response.status_code == 200
    services = {service["service_name"]: service for service in response.json()}
    assert services["catalog-service"]["endpoint"] == "http://127.0.0.1:8000/"
    assert services["order-service"]["operations"][0]["name"] == "create-order"


def test_catalog_lists_seeded_products_and_checks_availability(client: TestClient):
    products = client.get("/api/catalog/products")
    availability = client.post(
        "/api/catalog/availability",
        json={"product_id": "book-soa-101", "quantity": 2},
    )

    assert products.status_code == 200
    assert len(products.json()["products"]) == 3
    assert availability.json()["available"] is True
    assert availability.json()["available_quantity"] == 12


def test_order_provider_checks_catalog_and_persists_order(client: TestClient):
    response = client.post(
        "/api/orders",
        json={"items": [{"product_id": "book-soa-101", "quantity": 2}]},
    )

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "confirmed"
    saved = client.get(f"/api/orders/{order['order_id']}")
    assert saved.status_code == 200
    assert saved.json() == order


def test_order_provider_rejects_unavailable_product(client: TestClient):
    response = client.post(
        "/api/orders",
        json={"items": [{"product_id": "not-a-product", "quantity": 1}]},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_order_provider_reports_catalog_unavailable(client: TestClient):
    async def unavailable_catalog(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Catalog is offline", request=request)

    app.state.http_transport = httpx.MockTransport(unavailable_catalog)

    response = client.post(
        "/api/orders",
        json={"items": [{"product_id": "book-soa-101", "quantity": 1}]},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"
    assert response.json()["correlation_id"]


def test_order_provider_rejects_invalid_payload(client: TestClient):
    response = client.post(
        "/api/orders",
        json={"items": [{"product_id": "book-soa-101", "quantity": 0}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_service_call_propagates_correlation_id_to_provider(client: TestClient):
    correlation_id = "33333333-3333-4333-8333-333333333333"
    response = client.post(
        "/api/orders",
        headers={"X-Correlation-ID": correlation_id},
        json={"items": [{"product_id": "book-soa-101", "quantity": 1}]},
    )

    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == correlation_id


def test_database_data_survives_application_restart(tmp_path):
    original_database_path = app.state.database_path
    original_transport = app.state.http_transport
    app.state.database_path = str(tmp_path / "data" / "orders.sqlite3")
    app.state.http_transport = httpx.ASGITransport(app=app)
    try:
        with TestClient(app) as first_client:
            products = first_client.get("/api/catalog/products")
            order_response = first_client.post(
                "/api/orders",
                json={"items": [{"product_id": "book-soa-101", "quantity": 1}]},
            )
            assert products.status_code == 200
            assert len(products.json()["products"]) == 3
            assert order_response.status_code == 201
            order = order_response.json()

        with TestClient(app) as restarted_client:
            products_after_restart = restarted_client.get("/api/catalog/products")
            saved_order = restarted_client.get(f"/api/orders/{order['order_id']}")
            services_after_restart = restarted_client.get("/api/registry/services")

        assert products_after_restart.status_code == 200
        assert len(products_after_restart.json()["products"]) == 3
        assert saved_order.status_code == 200
        assert saved_order.json() == order
        assert services_after_restart.status_code == 200
        assert len(services_after_restart.json()) == 2
    finally:
        app.state.database_path = original_database_path
        app.state.http_transport = original_transport

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.registry.repository import ServiceRegistry


@pytest.fixture
def client(tmp_path):
    original_database_path = app.state.database_path
    app.state.database_path = str(tmp_path / "registry-tests.sqlite3")
    try:
        with TestClient(app) as test_client:
            app.state.service_registry = ServiceRegistry()
            yield test_client
    finally:
        app.state.database_path = original_database_path


def service_payload() -> dict:
    return {
        "service_name": "catalog-service",
        "description": "Product catalog and availability",
        "endpoint": "http://127.0.0.1:8001",
        "capabilities": ["Catalog", "availability"],
        "contract_url": "/openapi.json",
        "operations": [
            {
                "name": "list-products",
                "method": "GET",
                "path": "/api/catalog/products",
                "contract_version": "v1",
            }
        ],
    }


def test_register_list_get_and_discover_service(client: TestClient):
    response = client.post("/api/registry/services", json=service_payload())

    assert response.status_code == 201
    assert response.json()["status"] == "unknown"
    assert response.json()["capabilities"] == ["catalog", "availability"]

    assert client.get("/api/registry/services").json()[0]["service_name"] == "catalog-service"
    assert client.get("/api/registry/services/catalog-service").status_code == 200
    discovered = client.get(
        "/api/registry/discover",
        params={"capability": "CATALOG"},
    )
    assert [service["service_name"] for service in discovered.json()] == ["catalog-service"]


def test_duplicate_registration_returns_conflict(client: TestClient):
    payload = service_payload()
    assert client.post("/api/registry/services", json=payload).status_code == 201

    response = client.post("/api/registry/services", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_unknown_service_returns_structured_not_found(client: TestClient):
    response = client.get("/api/registry/services/missing-service")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_invalid_registration_returns_structured_validation_error(client: TestClient):
    payload = service_payload()
    payload["endpoint"] = "http://example.com"

    response = client.post("/api/registry/services", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["details"]


def test_discovery_returns_empty_list_for_unknown_capability(client: TestClient):
    response = client.get(
        "/api/registry/discover",
        params={"capability": "orders"},
    )

    assert response.status_code == 200
    assert response.json() == []

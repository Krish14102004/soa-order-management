import pytest
from pydantic import ValidationError

from app.contracts.catalog import AvailabilityRequest, ProductContract
from app.contracts.common import MessageEnvelope
from app.contracts.orders import CreateOrderRequest, OrderItemContract


def test_order_contract_requires_at_least_one_item():
    with pytest.raises(ValidationError):
        CreateOrderRequest(items=[])


def test_order_item_requires_positive_quantity():
    with pytest.raises(ValidationError):
        OrderItemContract(product_id="product-1", quantity=0)


def test_catalog_availability_requires_positive_quantity():
    with pytest.raises(ValidationError):
        AvailabilityRequest(product_id="product-1", quantity=-1)


def test_product_contract_rejects_negative_inventory():
    with pytest.raises(ValidationError):
        ProductContract(
            product_id="product-1",
            name="Sample",
            available_quantity=-1,
        )


def test_message_envelope_generates_distinct_message_metadata():
    envelope = MessageEnvelope[dict[str, str]](
        service="order-service",
        operation="create-order",
        payload={"status": "pending"},
    )

    assert envelope.message_id
    assert envelope.correlation_id
    assert envelope.contract_version == "v1"

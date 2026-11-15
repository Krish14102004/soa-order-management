import json
import sqlite3
from pathlib import Path

from app.contracts.orders import OrderItemContract, OrderResponse, OrderStatus


class OrderRepository:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS customer_orders (
                    order_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_order(self, order: OrderResponse) -> OrderResponse:
        items_json = json.dumps(
            [item.model_dump(mode="json") for item in order.items],
            separators=(",", ":"),
        )
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO customer_orders (order_id, status, items_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(order.order_id),
                    order.status.value,
                    items_json,
                    order.created_at.isoformat(),
                ),
            )
        return order

    def get_order(self, order_id: str) -> OrderResponse | None:
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT order_id, status, items_json, created_at
                FROM customer_orders
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()
        if row is None:
            return None
        return OrderResponse(
            order_id=row[0],
            status=OrderStatus(row[1]),
            items=[OrderItemContract.model_validate(item) for item in json.loads(row[2])],
            created_at=row[3],
        )


__all__ = ["OrderRepository"]

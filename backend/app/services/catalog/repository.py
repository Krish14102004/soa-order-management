import sqlite3
from pathlib import Path

from app.contracts.catalog import ProductContract

SEED_PRODUCTS = (
    ProductContract(
        product_id="book-soa-101",
        name="Service-Oriented Architecture",
        description="A practical introduction to service boundaries and contracts.",
        available_quantity=12,
    ),
    ProductContract(
        product_id="mug-blue",
        name="Blue Ceramic Mug",
        description="A reusable ceramic mug.",
        available_quantity=20,
    ),
    ProductContract(
        product_id="notebook-grid",
        name="Grid Notebook",
        description="A compact notebook with grid paper.",
        available_quantity=8,
    ),
)


class CatalogRepository:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog_products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    available_quantity INTEGER NOT NULL CHECK (available_quantity >= 0)
                )
                """
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO catalog_products
                    (product_id, name, description, available_quantity)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        product.product_id,
                        product.name,
                        product.description,
                        product.available_quantity,
                    )
                    for product in SEED_PRODUCTS
                ],
            )

    def list_products(self) -> list[ProductContract]:
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT product_id, name, description, available_quantity
                FROM catalog_products
                ORDER BY product_id
                """
            ).fetchall()
        return [
            ProductContract(
                product_id=row[0],
                name=row[1],
                description=row[2],
                available_quantity=row[3],
            )
            for row in rows
        ]

    def get_product(self, product_id: str) -> ProductContract | None:
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT product_id, name, description, available_quantity
                FROM catalog_products
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchone()
        if row is None:
            return None
        return ProductContract(
            product_id=row[0],
            name=row[1],
            description=row[2],
            available_quantity=row[3],
        )

    def check_availability(self, product_id: str, quantity: int) -> tuple[bool, int]:
        product = self.get_product(product_id)
        if product is None:
            return False, 0
        return product.available_quantity >= quantity, product.available_quantity

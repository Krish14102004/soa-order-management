"""Central configuration for local services and persistence."""

import math
import os

APP_NAME = os.getenv("APP_NAME", "SOA Order Management")
APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./soa_orders.db")
CATALOG_SERVICE_URL = os.getenv(
    "CATALOG_SERVICE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
ORDER_SERVICE_URL = os.getenv(
    "ORDER_SERVICE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
ESB_TIMEOUT_SECONDS = float(os.getenv("ESB_TIMEOUT_SECONDS", "3"))
if not math.isfinite(ESB_TIMEOUT_SECONDS) or not 0 < ESB_TIMEOUT_SECONDS <= 60:
    raise ValueError("ESB_TIMEOUT_SECONDS must be greater than 0 and at most 60")

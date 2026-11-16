# API Contracts

All provider and dispatch contracts in this phase are version `v1`. Pydantic models reject unknown fields. The registry publishes the Catalog and Order operation metadata during application startup.

## Service registry

| Method | Path | Request | Response |
|---|---|---|---|
| `POST` | `/api/registry/services` | `ServiceRegistration` | `ServiceDescriptor` (`201`) |
| `GET` | `/api/registry/services` | — | `ServiceDescriptor[]` |
| `GET` | `/api/registry/services/{service_name}` | — | `ServiceDescriptor` |
| `GET` | `/api/registry/discover?capability={capability}` | — | matching `ServiceDescriptor[]` |

`ServiceRegistration` includes a kebab-case `service_name`, description, local HTTP endpoint, unique capabilities, local contract path, and one or more operations. Each operation has a name, `GET` or `POST` method, absolute path, and contract version. Registered descriptors add an `unknown` health status and registration timestamp. Duplicate names return `409`; an unknown service returns `404`; invalid input returns `422`. Error responses use `ErrorResponse`.

The registry only stores metadata. Discovery by service name uses the service detail path; capability matching is case-insensitive. An empty capability search returns an empty list.

## Catalog provider

- `ProductContract`: `product_id`, `name`, optional `description`, and non-negative `available_quantity`.
- `ProductListResponse`: `products: ProductContract[]`.
- `AvailabilityRequest`: `product_id` and positive `quantity`.
- `AvailabilityResponse`: `product_id`, `requested_quantity`, `available`, and current `available_quantity`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/catalog/products` | List synthetic catalog products. |
| `GET` | `/api/catalog/products/{product_id}` | Get one product; returns `404` when missing. |
| `POST` | `/api/catalog/availability` | Check requested quantity without changing inventory. |

The catalog seeds three synthetic products at first database initialization. The database is shared as a local file but its product table is owned by the Catalog Service. Availability checks do not reserve or decrement stock.

## Order provider

- `CreateOrderRequest`: one to 100 `OrderItemContract` entries, each with a `product_id` and positive `quantity`.
- `OrderResponse`: UUID `order_id`, `status` (`pending`, `confirmed`, or `rejected`), submitted items, and `created_at`.
- `OrderListResponse`: `orders: OrderResponse[]`, ordered newest first.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/orders` | Check each item against Catalog, then persist a confirmed order (`201`). Insufficient/unknown product availability returns `409`; Catalog unavailable/timeout returns `503`/`504`. |
| `GET` | `/api/orders` | Return persisted Order history, newest first. |
| `GET` | `/api/orders/{order_id}` | Retrieve a saved order; returns `404` when missing. |

The Order Service owns its SQLite order table and calls Catalog over HTTP for availability. Monetary totals are intentionally not part of v1 because the PRD does not define pricing or currency.

## Common contracts

- `MessageEnvelope[T]`: message and correlation UUIDs, service, operation, contract version, and typed payload.
- `ErrorResponse`: an error code/message, optional field-level details, and an optional correlation ID.
- `MessageTrace`: message/correlation IDs, timestamp, source, destination, operation, result, HTTP status, and duration.

## ESB / gateway

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/esb/dispatch` | Validate a v1 envelope and operation payload, resolve the provider via the registry, route over HTTP, validate the provider response, and normalize errors. |
| `GET` | `/api/esb/traces?limit=50` | Return recent traces; `limit` is 1–100 and history is bounded to the latest 200 messages. |

Dispatch supports the registered Catalog operations `list-products`, `get-product`, and `check-availability`, and Order operations `create-order`, `list-orders`, and `get-order`. The consumer discovers `list-orders` from the Order Service registry descriptor and invokes it through the ESB; it does not call the provider endpoint directly. An unknown service/operation returns `404`; an unsupported gateway operation returns `501`; contract mismatch or invalid payload returns `422`; provider timeout returns `504`; provider unavailability returns `503`; and malformed provider output returns `502`. The response preserves the message and correlation IDs. The correlation ID is also propagated in `X-Correlation-ID`.

The provider URLs and timeout are configurable with `CATALOG_SERVICE_URL`, `ORDER_SERVICE_URL`, and `ESB_TIMEOUT_SECONDS`. Both service URLs must be local loopback HTTP URLs in this demo.

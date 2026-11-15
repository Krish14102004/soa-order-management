# Architecture Decisions

Record dated decisions here. Each entry should include context, decision, alternatives considered, and consequences.

## Initial decisions
- Initial transport: REST/HTTP.
- Initial persistence: SQLite.
- ESB: lightweight custom routing/mediation layer for educational demonstration.
- Initial data: synthetic seed products; no external dataset required.

## 2026-11-15 — Phase 2 registry and contract scope
- Context: The registry must support registration and discovery before provider persistence and orchestration are implemented.
- Decision: Use an in-memory registry for Phase 2; persistence is deferred to Phase 5. Registration is unauthenticated and demo-only, so only trusted local users should access it. Registered provider endpoints are restricted to unauthenticated HTTP on localhost or loopback IPs. The registry does not call those endpoints.
- Contract scope: v1 order items contain product IDs and quantities; monetary totals are omitted until pricing and currency are specified.
- Consequences: Registry contents disappear on restart. A future deployment requiring remote providers must add an explicit trusted-host policy and an authorization mechanism before opening registration beyond the local demo.

## 2026-11-15 — Phase 3 provider and gateway implementation
- Context: Phase 3 needs real provider calls, order persistence, and routing evidence while keeping setup local and small.
- Decision: Use SQLite via Python's standard library. The Catalog and Order modules own separate tables in the same local database file. The registry is populated with both providers at startup; its metadata remains process-local.
- Transport: Use HTTPX for ESB-to-provider and Order-to-Catalog HTTP calls, with environment-configurable loopback service URLs and a bounded timeout. The gateway validates v1 operation payloads and responses against shared contracts.
- Inventory behavior: Order placement checks availability but does not reserve/decrement stock. Reservation and compensation are deferred because v1 has no reservation contract; repeated orders can therefore exceed the displayed stock.
- Consequences: This remains a single-process educational deployment. Separate provider processes can be configured later, but their endpoints must remain explicitly trusted and local for the demo.

## 2026-11-15 — Phase 5 local persistence and orchestration
- Context: Phase 5 required reproducible local startup, clear persistence behavior, and consideration of Docker Compose.
- Decision: Keep standard-library SQLite with separate Catalog and Order tables in one configurable database file. Initialize schemas and insert only missing seed products during application startup. Use environment variables for the database path, provider base URLs, and bounded HTTP timeout. Do not add Docker Compose for the current single-backend/Vite workflow because it has no external infrastructure dependency.
- Alternatives considered: Add a containerized frontend/backend stack or split providers into separate containers. Neither improves the current local educational workflow enough to justify extra setup and networking configuration.
- Consequences: Orders and Catalog records persist in SQLite across restarts; registry entries and message traces are process-local and are recreated/reset at startup. A new database path provides a clean demo without deleting existing data. The local process can be stopped with Ctrl+C; SQLite connections are scoped to individual operations.

# Architecture Document
# SOA-Based Distributed Order Management System

## 1. Architecture Style
A service-oriented application with independently bounded Catalog and Order providers, a Service Registry, a logical ESB/API gateway, and a React consumer UI.

The first version uses REST/HTTP for transport. The ESB is a dedicated mediation boundary; it is not a business service.

## 2. High-Level Flow
1. Catalog and Order providers start and register their metadata.
2. The consumer requests service descriptions from the registry.
3. The consumer reads the published operation and data contracts.
4. The consumer sends an order request to the ESB.
5. The ESB identifies the target provider, validates/routs the message, and adds or propagates a correlation ID.
6. Order Service performs order logic and obtains product availability through the Catalog service boundary.
7. The ESB returns a normalized response to the consumer.
8. The UI displays the result and trace.

## 3. Component Responsibilities
- **Consumer UI:** customer-facing application; discovers services and invokes them through published contracts.
- **Service Registry:** stores discoverable service metadata and contract references. It does not execute business logic.
- **ESB / Gateway:** routes messages, applies cross-cutting policies, records trace metadata, and normalizes errors.
- **Catalog Service:** owns product catalogue and availability operations.
- **Order Service:** owns order creation and order status.
- **Contract definitions:** request/response schemas and API descriptions shared as interface agreements.
- **Persistence:** SQLite for initial local development; ownership is separated by service repository/module even if one database file is used initially.

## 4. Suggested Folder Structure

```text
soa-order-management/
├── PRD.md                         # Product scope, users, features, requirements
├── architecture.md                # Architecture, flow, stack, folder map
├── rules.md                        # Engineering rules and AI boundaries
├── phases.md                       # Milestones and phase exit criteria
├── design.md                       # UI visual system
├── memory.md                       # Ongoing progress log; initially empty except instructions
├── AI_AGENT_PROMPT.md              # Prompt for an implementation-planning AI agent
├── README.md                       # Setup, run, test, and demo instructions
├── .env.example                    # Documented environment variables; Phase 1
├── .gitignore                      # Ignore generated files and secrets; Phase 1
├── docker-compose.yml               # Local orchestration; Phase 5
├── backend/
│   ├── requirements.txt            # Python dependencies; Phase 1
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point; Phase 1
│   │   ├── core/
│   │   │   ├── config.py            # Environment/config loading; Phase 1
│   │   │   ├── errors.py             # Shared structured error definitions; Phase 2
│   │   │   └── logging_config.py     # Logging and correlation context; Phase 2
│   │   ├── contracts/
│   │   │   ├── common.py             # Shared envelope/error schemas; Phase 2
│   │   │   ├── catalog.py            # Catalog request/response contracts; Phase 2
│   │   │   └── orders.py              # Order request/response contracts; Phase 2
│   │   ├── registry/
│   │   │   ├── models.py             # Registry service metadata model; Phase 2
│   │   │   ├── repository.py          # Registry persistence/access; Phase 2
│   │   │   └── router.py              # Register/list/discover endpoints; Phase 2
│   │   ├── esb/
│   │   │   ├── router.py               # Consumer-facing dispatch endpoint; Phase 3
│   │   │   ├── routing.py              # Resolve destination from registry; Phase 3
│   │   │   ├── policies.py             # Content type, version, timeout policies; Phase 3
│   │   │   └── tracing.py              # Correlation IDs and message trace; Phase 3
│   │   ├── services/
│   │   │   ├── catalog/
│   │   │   │   ├── models.py            # Catalog-owned domain models; Phase 3
│   │   │   │   ├── repository.py        # Catalog data access; Phase 3
│   │   │   │   └── router.py             # Catalog provider API; Phase 3
│   │   │   └── orders/
│   │   │       ├── models.py             # Order-owned domain models; Phase 3
│   │   │       ├── repository.py        # Order data access; Phase 3
│   │   │       ├── logic.py              # Order business rules; Phase 3
│   │   │       └── router.py             # Order provider API; Phase 3
│   │   └── database/
│   │       ├── connection.py             # Database connection/session; Phase 3
│   │       └── init_db.py                # Initial schema/seed setup; Phase 3
│   └── tests/
│       ├── test_contracts.py             # Contract validation tests; Phase 2
│       ├── test_registry.py              # Registry tests; Phase 2
│       ├── test_esb.py                   # Routing/policy tests; Phase 3
│       └── test_order_flow.py            # End-to-end workflow tests; Phase 4
├── frontend/
│   ├── package.json                    # Frontend scripts/dependencies; Phase 1
│   ├── index.html                      # Browser entry HTML; Phase 1
│   └── src/
│       ├── main.tsx                    # React bootstrap; Phase 1
│       ├── App.tsx                     # Main app composition; Phase 1
│       ├── styles/
│       │   └── global.css              # Global tokens and resets; Phase 1
│       ├── types/
│       │   └── api.ts                  # Typed API contract representations; Phase 2
│       ├── services/
│       │   └── apiClient.ts            # HTTP client boundary; Phase 2
│       ├── components/
│       │   ├── layout/                 # Header, navigation, page shell; Phase 1
│       │   ├── architecture/           # SOA diagram and component cards; Phase 4
│       │   ├── registry/               # Registry/discovery views; Phase 4
│       │   ├── orders/                 # Product and order UI; Phase 4
│       │   └── trace/                  # Message trace/timeline; Phase 4
│       └── pages/
│           ├── DashboardPage.tsx        # Architecture overview; Phase 4
│           ├── ServicesPage.tsx         # Discover registered services; Phase 4
│           └── OrdersPage.tsx           # Browse and submit orders; Phase 4
└── docs/
    ├── api-contracts.md                # Human-readable API/contract index; Phase 2
    ├── demo-script.md                  # Presentation walkthrough; Phase 6
    └── decisions.md                    # Architecture decision records; ongoing
```

## 5. Technology Stack
- Frontend: React, TypeScript, Vite.
- Backend: Python, FastAPI, Pydantic.
- Persistence: SQLite initially; SQLAlchemy or SQLModel only if useful.
- API: REST over HTTP; OpenAPI generated by FastAPI.
- Contract validation: Pydantic models and JSON Schema where external schema documents are useful.
- Testing: Pytest; frontend tests can be added if UI complexity warrants them.
- Local orchestration: Docker Compose after local execution is stable.

## 6. Contract and Message Design
Use a consistent message envelope where appropriate:
- `message_id`: unique request identifier.
- `correlation_id`: links request and response logs.
- `service`: target logical service name.
- `operation`: requested operation.
- `contract_version`: interface version.
- `payload`: operation-specific data.

Do not wrap every REST request in an unnecessary custom envelope if it makes normal HTTP APIs harder to understand. Keep the envelope for ESB dispatch and tracing where it adds value.

## 7. Boundaries
- The UI must not access provider databases.
- The registry stores metadata, not provider business data.
- The ESB routes and applies policies; it must not contain order calculation or inventory business rules.
- Order Service owns order creation and status.
- Catalog Service owns product information and availability.
- Consumers depend on contracts, not provider implementation classes.
- Keep service-to-service calls explicit and configurable.

## 8. Initial API Sketch
- `GET /api/registry/services`
- `POST /api/registry/services`
- `GET /api/registry/services/{service_name}`
- `GET /api/catalog/products`
- `GET /api/catalog/products/{product_id}`
- `POST /api/esb/dispatch`
- `POST /api/orders` (provider endpoint, preferably reached through ESB by the consumer)
- `GET /api/orders/{order_id}`

Finalize paths and payloads before implementing dependent frontend code.

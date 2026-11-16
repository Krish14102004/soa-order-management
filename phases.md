# Implementation Phases

Status values: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETED`.

## Phase 0 — Requirements and Repository Review
**Status:** COMPLETED (initial planning package)

Tasks:
- Confirm the e-commerce/mail-order demonstration scenario.
- Define users, features, requirements, and acceptance criteria.
- Agree on stack and service boundaries.
- Review this plan before implementation.

Exit criteria:
- PRD and architecture are reviewed and approved.

## Phase 1 — Repository and Development Environment
**Status:** COMPLETED

Tasks:
- Create frontend and backend project skeletons.
- Add dependency manifests, environment example, ignore rules, and README.
- Configure FastAPI entry point and React/Vite entry point.
- Verify both applications start locally.

Human tasks:
- Python 3.13, Node.js, and npm were available; local virtual environment and frontend dependencies were installed.

Exit criteria:
- Backend health endpoint responds. **Verified by developer.**
- Frontend loads in a browser. **Verified by developer.**
- Setup instructions work from a clean environment. **Backend test and frontend build/run verified by developer.**

## Phase 2 — Contracts and Service Registry
**Status:** COMPLETED

Tasks:
- Define Catalog and Order request/response contracts.
- Define common message/error metadata.
- Implement service registration, listing, and discovery.
- Publish contract references and service metadata.
- Add unit tests.

Exit criteria:
- Services can be registered and discovered. **Verified by registry tests.**
- Invalid metadata/payloads are rejected predictably. **Verified by contract and API validation tests.**
- Contract and registry tests pass. **11 backend tests pass; frontend production build succeeds.**

## Phase 3 — Providers and ESB
**Status:** COMPLETED

Tasks:
- Implement Catalog Service.
- Implement Order Service and persistence.
- Implement ESB dispatch and destination resolution.
- Add correlation IDs, routing logs, timeout handling, and structured errors.
- Keep business logic out of the ESB.
- Add service and ESB tests.

Exit criteria:
- A request sent to the ESB reaches the correct provider. **Verified by dispatch tests.**
- Provider response returns through the gateway. **Verified by typed provider response tests.**
- Failure cases are handled and traceable. **Verified for invalid contracts, unknown services/operations, timeout, unavailability, and provider business errors.**

## Phase 4 — Consumer UI and End-to-End Workflow
**Status:** COMPLETED

Tasks:
- Build dashboard and architecture view.
- Build registry/discovery screen.
- Build product browsing and order placement UI.
- Display lifecycle steps and message traces.
- Connect UI to real backend APIs.
- Add end-to-end tests.

Exit criteria:
- A user can discover services and place an order through the UI. **Verified in a local browser.**
- The request uses published contracts and ESB routing. **Verified by a browser order and gateway trace.**
- UI displays real response and trace data. **Verified for success and unavailable-inventory error responses.**

## Phase 5 — Persistence, Configuration, and Local Orchestration
**Status:** COMPLETED

Tasks:
- Finalize database initialization and seed data. **Verified: startup initializes tables and seeds missing products idempotently; products and orders survive an application restart.**
- Add environment-driven configuration. **Verified/documented: database path, provider URLs, and bounded service timeout are configurable through process environment variables.**
- Evaluate Docker Compose. **Not added: the demo has no external infrastructure and its single backend/Vite local workflow is simpler without containers.**
- Verify clean startup and shutdown. **Verified through separate TestClient lifespan startup/shutdown cycles; database connections close per operation.**
- Document reset and troubleshooting steps. **Documented in README.md, including a non-destructive fresh-database option.**

Exit criteria:
- Application can be started consistently from documented commands. **Verified through the documented local workflow and backend lifespan tests.**
- Data ownership and persistence limitations are documented. **Catalog and Order own separate tables; SQLite records persist, while registry and traces are in-memory.**

## Phase 6 — Quality, Demonstration, and Submission
**Status:** COMPLETED

Tasks:
- Run all tests and fix defects. **Verified at Phase 6 completion: 28 backend tests pass and the frontend production build succeeds.**
- Check validation, unknown service, provider down, timeout, and invalid contract cases. **Covered by ESB/provider tests; successful and business-error UI flows were browser-verified in Phase 4.**
- Prepare architecture diagram and demo script. **The dashboard architecture map is complete; `docs/demo-script.md` documents the local walkthrough.**
- Explain how each of the four SOA tenets is implemented. **Documented in the demo script with component evidence.**
- Capture screenshots only after the application works. **No screenshots committed; none are required for the local walkthrough.**
- Review documentation for accuracy. **README, architecture, phase tracker, API contracts, decisions, and demo script reviewed against the implementation.**

Exit criteria:
- Acceptance criteria in `PRD.md` are met. **Verified by backend/API tests and prior browser workflow.**
- Demo can be completed from a clean start. **Documented startup, fresh database, health check, order, and error demonstration steps.**
- No unverified claims remain in documentation. **Test counts and persistence/registry limitations are stated explicitly.**

## Working Agreement
- Complete phases in order unless a dependency requires parallel work.
- Do not mark a phase completed until its exit criteria are verified.
- Ask the developer for required manual actions with exact steps.
- Update `memory.md` after each meaningful work session.

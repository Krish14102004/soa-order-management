<!--
PROJECT MEMORY / PROGRESS LOG

Keep this file empty of progress entries at project initialization.
Update it regularly after every meaningful implementation session.

Always record:
1. What has been completed (with exact files/modules).
2. What is currently being worked on (the exact file or task).
3. What remains to be done next.
4. Commands/tests actually run and their real outcomes.
5. Blockers or actions required from the developer.
6. Any approved architecture/requirement decisions.

Do not claim work is complete unless it has been implemented and verified.
-->

## 2026-11-15 — Phase 4 completed

- Completed: Implemented a responsive React operations dashboard with Dashboard, Service Registry, Orders, and Message Trace views. The UI loads provider metadata from the registry, discovers Catalog and Order capabilities, sends product-list and order calls through the ESB using the published operation contract version, and displays returned orders, correlation IDs, lifecycle state, and routing traces. Loading, empty, API error, unavailable inventory, and success states are represented.
- Updated: `frontend/src/App.tsx`, `frontend/src/services/apiClient.ts`, `frontend/src/types/api.ts`, `frontend/src/styles/global.css`, `frontend/.env.example`, `README.md`, and `phases.md`.
- Current status: Phases 1–4 are marked `COMPLETED`. Phase 5 (configuration/persistence/orchestration review) and Phase 6 (final QA/demo) remain.
- Commands actually checked: `npm.cmd run build` succeeded with Vite 8.3.8 and TypeScript 7.0.2 (two informational lucide-react module-directive warnings). `.\.venv\Scripts\python.exe -m pytest -q` passed all 27 tests (one Starlette/httpx deprecation warning).
- Browser verification: Opened the local Vite page, confirmed the dashboard loaded live registry and catalog data, viewed both provider records, added a product and placed an order through the UI, confirmed order/correlation IDs, and saw the resulting trace. Submitted a quantity above reported availability and confirmed the structured `409` message appeared in the UI.
- Runtime note: The backend port was already occupied by an existing backend process; an attempted second start exited with Windows error 10048. Verification used the existing server, and the frontend dev server started for browser verification.
- Limitations: Product/order persistence and trace behavior remain as documented after Phase 3; the UI is local-demo focused, with API origin configurable through `VITE_API_BASE_URL`.

## 2026-11-15 — Phase 5 completed

- Completed: Added a backend lifecycle regression test that starts the application twice against the same nested SQLite path, verifies seeded Catalog data is not duplicated, verifies an Order remains retrievable, and confirms the in-memory registry is republished after restart. Documented persistence ownership, environment overrides, a non-destructive fresh-database workflow, port troubleshooting, and clean shutdown steps.
- Updated: `backend/tests/test_providers.py`, `README.md`, `phases.md`, `memory.md`, and `docs/decisions.md`.
- Current status: Phases 1–5 are marked `COMPLETED`. Phase 6 is next: final quality checks, demo walkthrough, SOA tenet evidence, and submission review.
- Commands actually checked: `.\.venv\Scripts\python.exe -m pytest tests\test_providers.py -q` passed 8 tests; `.\.venv\Scripts\python.exe -m pytest -q` passed all 28 tests.
- Test result: One existing Starlette/httpx deprecation warning remains; no test failures.
- Orchestration decision: Docker Compose was evaluated and omitted because no external service/container is needed for the single-process local backend and Vite workflow.
- Blockers: None. No external dataset, credentials, or installation is required.
- Additional verification: A temporary-database smoke check with environment overrides completed startup, health and catalog requests, successful order creation, and TestClient shutdown. Temporary SQLite file and environment overrides were cleaned up.

## 2026-11-15 — Phase 6 completed

- Completed: Reviewed final API/provider failure-path tests, aligned the architecture folder map with the no-Compose decision, and replaced the placeholder demo outline with a Windows-first walkthrough covering startup, dashboard architecture, registry discovery, contract inspection, real order dispatch, correlation traces, validation errors, and the four SOA tenets.
- Updated: `architecture.md`, `docs/demo-script.md`, `README.md`, `phases.md`, and `memory.md`.
- Current status: Phases 1–6 are marked `COMPLETED`. The application is ready for local demonstration and submission review.
- Commands actually checked: `.\.venv\Scripts\python.exe -m pytest -q` passed 28 tests. `npm.cmd run build` passed. Environment-configured startup/order/shutdown smoke check passed with a temporary SQLite database.
- Test result: The backend suite reports one existing Starlette/httpx deprecation warning; the frontend build reports two informational Lucide module-directive warnings. No failures.
- Failure-path evidence: Existing tests cover payload and version validation, unknown services/operations, provider unavailable/timeout, business conflict, and correlation traces. Phase 4 browser verification covered successful ordering and visible 409 errors.
- Blockers: None. No screenshots were committed; the demo script is usable without them.

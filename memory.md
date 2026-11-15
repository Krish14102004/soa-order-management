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

## 2026-11-15 — Phase 3 completed

- Completed: Implemented Catalog product and availability endpoints backed by synthetic SQLite seed data; Order creation/status endpoints backed by a separately owned order table; provider publication at app startup; HTTP ESB discovery/routing with contract validation, response validation, correlation propagation, error normalization, and bounded trace history.
- Updated: `backend/app/core/config.py`, `backend/app/contracts/catalog.py`, `backend/app/contracts/orders.py`, `backend/app/services/catalog/`, `backend/app/services/orders/`, `backend/app/esb/`, `backend/app/main.py`, `backend/requirements.txt`, `backend/tests/test_registry.py`, `backend/tests/test_esb.py`, `backend/tests/test_providers.py`, `.env.example`, `docs/api-contracts.md`, `docs/decisions.md`, `README.md`, and `phases.md`.
- Current status: Phases 1, 2, and 3 are marked `COMPLETED`. Phase 4 is next: connect the React consumer and render registry/order/trace data.
- Commands actually checked: `.\.venv\Scripts\python.exe -m pytest` passed 27 tests. `npm.cmd run build` passed with Vite 8.3.8. The Python environment is 3.13; Python 3.11+ is required by the code (`StrEnum`).
- Test coverage: Provider registration, seeded Catalog list/availability, Order persistence and validation, successful ESB dispatch, schema/version rejection, unknown service/operation, provider timeout/unavailability/business errors, Order-to-Catalog unavailability, correlation propagation, and trace output.
- Limitations: Catalog availability is checked but not reserved/decremented; repeated orders can exceed stock. Registry and traces are in memory. Provider registry endpoints and timeout are configurable but constrained to local loopback HTTP for this demo. Frontend API integration remains Phase 4.

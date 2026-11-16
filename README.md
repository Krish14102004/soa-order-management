# SOA-Based Distributed Order Management System

An educational SOA implementation demonstrating service providers, a service consumer, service registry, service/data contracts, and an ESB-style routing layer through an order-processing scenario.

## Project documents

Read these before implementation:
- `PRD.md` — scope, requirements, and acceptance criteria.
- `architecture.md` — component boundaries, flow, stack, and folder map.
- `rules.md` — engineering constraints and AI boundaries.
- `phases.md` — implementation milestones and exit criteria.
- `design.md` — visual design system.
- `memory.md` — progress log.
- `AI_AGENT_PROMPT.md` — implementation assistant guidance.
- `docs/demo-script.md` — verified local demonstration walkthrough.

## Current status

Phases 1–6 are implemented and verified. The React consumer discovers providers through the registry, sends catalog, order, and order-history requests through the ESB, and displays real orders and message traces. SQLite-backed product and order data survives backend restarts; registry entries and ESB traces are recreated in memory at startup. See [docs/demo-script.md](docs/demo-script.md) for a Windows-first walkthrough.

## Prerequisites

- Python 3.11 or later.
- Node.js 22.12 or later and npm.

Check the installed tools from PowerShell:

```powershell
py --version
node --version
npm.cmd --version
```

In PowerShell, use `npm.cmd` if the `npm` command is blocked by the local script execution policy.

## Run the backend

In a PowerShell terminal:

```powershell
cd D:\SOA_Order_Management_Starter\soa-order-management\backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Replace `3.13` with your installed Python version if it is 3.11 or later.

The test command should report 31 passing tests. Leave the backend running, then check it from another terminal:

```powershell
curl.exe -i http://127.0.0.1:8000/health
```

Expected response: HTTP 200 with `{"status":"ok","service":"soa-order-management-api"}`. Startup creates the SQLite tables, seeds three synthetic Catalog products, and publishes both providers in the registry.

## Try provider discovery and ESB dispatch

List the registered providers:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/registry/services
```

Submit an order through the ESB:

```powershell
$envelope = @{
    service = "order-service"
    operation = "create-order"
    contract_version = "v1"
    payload = @{ items = @(@{ product_id = "book-soa-101"; quantity = 1 }) }
}
$body = $envelope | ConvertTo-Json -Depth 6
Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/api/esb/dispatch `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

The response contains the correlation ID, provider HTTP status, and order payload. View persisted order history through the published Order Service operation via ESB:

```powershell
$historyEnvelope = @{
    service = "order-service"
    operation = "list-orders"
    contract_version = "v1"
    payload = @{}
}
$historyBody = $historyEnvelope | ConvertTo-Json -Depth 6
Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/api/esb/dispatch `
    -Method Post `
    -ContentType "application/json" `
    -Body $historyBody
```

In the consumer, select **Order History** to inspect saved order IDs, placement times, items, and statuses. The history is read from the Order Service's SQLite repository; it is not reconstructed from browser state.

View recent routing traces with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/esb/traces
```

## Run the frontend

In a second PowerShell terminal:

```powershell
cd D:\SOA_Order_Management_Starter\soa-order-management\frontend
npm.cmd ci
npm.cmd run build
npm.cmd run dev -- --host 127.0.0.1
```

The build should complete without TypeScript or Vite errors. Open <http://127.0.0.1:5173/> to use the dashboard, inspect discovered services and traces, and place a real order through the ESB.

The consumer uses `VITE_API_BASE_URL` for the backend origin and defaults to `http://127.0.0.1:8000`. To override it, copy `frontend\.env.example` to `frontend\.env.local`, edit the URL, and restart Vite.

## Configuration note

The app reads `DATABASE_PATH`, `CATALOG_SERVICE_URL`, `ORDER_SERVICE_URL`, and `ESB_TIMEOUT_SECONDS` from the process environment. Defaults are documented in the root `.env.example`; the application does not automatically load that file. Set environment variables in the same PowerShell window before starting Uvicorn if you need non-default values. Service URLs must point to local loopback HTTP endpoints; the timeout must be greater than zero and at most 60 seconds.

The default database path, `.\soa_orders.db`, is relative to the backend working directory used in the commands above. On startup, the app creates missing tables and inserts the three synthetic Catalog products only when their IDs are absent. Catalog products and orders use separate tables in this SQLite file and persist across backend restarts. The Catalog Service checks stock but does not reserve or decrement inventory; repeated orders can exceed the displayed stock. The registry and ESB traces are in-memory and reset whenever the backend restarts. Provider registration is intended for trusted local demo use only.

To start with a separate, clean database without deleting existing data, use a different file path in the backend terminal before starting Uvicorn:

```powershell
$env:DATABASE_PATH = ".\soa_orders_fresh.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The new file receives the usual synthetic seed products. To return to the default path in that terminal, run `Remove-Item Env:DATABASE_PATH` after stopping the server. Keep each chosen database file if you want to preserve its orders.

### Configuration example

Set overrides in the same PowerShell window that starts Uvicorn. For example, to run the backend on port 8001 when port 8000 is occupied:

```powershell
$env:DATABASE_PATH = ".\soa_orders_port8001.sqlite3"
$env:CATALOG_SERVICE_URL = "http://127.0.0.1:8001"
$env:ORDER_SERVICE_URL = "http://127.0.0.1:8001"
$env:ESB_TIMEOUT_SECONDS = "3"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

For the frontend in this setup, set `VITE_API_BASE_URL=http://127.0.0.1:8001` in `frontend\.env.local` and restart Vite. These provider URLs point back to the same API process; separate provider processes are not required for the local demo.

### Troubleshooting and shutdown

- **Backend connection error:** Confirm the backend is running and `curl.exe -i http://127.0.0.1:8000/health` returns HTTP 200. If using another port, use it consistently for the backend URL settings and frontend `VITE_API_BASE_URL`.
- **Port already in use:** Do not start a second backend on that port. Use the port-8001 configuration above, or stop the backend you started in its own terminal with `Ctrl+C`.
- **Python cannot import `app`:** Run backend commands from the `backend` directory as shown; the documented module invocation is `python.exe -m pytest`.
- **Frontend still uses an old backend URL:** Stop and restart Vite after changing `frontend\.env.local`.
- **Stop the services:** Press `Ctrl+C` in each terminal running Uvicorn or Vite. Database connections are opened per operation and closed by SQLite context managers; there is no persistent database connection to shut down separately.

## Next

All six implementation phases are complete. Run the tests and follow [docs/demo-script.md](docs/demo-script.md) to demonstrate the application.

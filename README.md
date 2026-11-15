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

## Current status

Phases 1–3 are implemented and verified. The backend exposes the Catalog and Order providers, a demo-only registry, and an HTTP ESB with correlation-aware traces. The React UI remains a scaffold; connecting it to these APIs is Phase 4.

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

The test command should report 27 passing tests. Leave the backend running, then check it from another terminal:

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

The response contains the correlation ID, provider HTTP status, and order payload. View recent routing traces with:

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

The build should complete without TypeScript or Vite errors. Open <http://127.0.0.1:5173/> to see the overview shell. The UI is still a scaffold; API-backed discovery, order placement, routing, and traces are Phase 4 work.

## Configuration note

The app reads `DATABASE_PATH`, `CATALOG_SERVICE_URL`, `ORDER_SERVICE_URL`, and `ESB_TIMEOUT_SECONDS` from the process environment. Defaults are documented in the root `.env.example`; the application does not automatically load that file. Set environment variables in the same PowerShell window before starting Uvicorn if you need non-default values. Service URLs must point to local loopback HTTP endpoints; the timeout must be greater than zero and at most 60 seconds.

Orders and products use separate tables in the local SQLite file. The Catalog Service checks stock but does not reserve or decrement inventory; repeated orders can exceed the displayed stock. The registry is in-memory and provider registration is intended for trusted local demo use only.

## Next

Phase 3 is complete. Phase 4 connects the React consumer to the registry and ESB APIs and displays real orders and message traces.

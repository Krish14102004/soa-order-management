# Demonstration Script

This 8–10 minute walkthrough shows the complete SOA request lifecycle using the local React consumer, registry, ESB, Catalog provider, and Order provider.

## 1. Start a clean local demo

In a PowerShell terminal:

```powershell
cd D:\SOA_Order_Management_Starter\soa-order-management\backend
$demoDatabase = ".\soa_orders_demo_$([DateTime]::Now.ToString('yyyyMMdd_HHmmss')).sqlite3"
$env:DATABASE_PATH = $demoDatabase
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The timestamped database path keeps existing local orders untouched. The test suite should report 28 passing tests. In a second PowerShell terminal, start the consumer:

```powershell
cd D:\SOA_Order_Management_Starter\soa-order-management\frontend
npm.cmd run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173/>. Confirm the backend health endpoint responds:

```powershell
curl.exe -i http://127.0.0.1:8000/health
```

Expected: HTTP 200 and `{"status":"ok","service":"soa-order-management-api"}`. Startup creates the schema, seeds three synthetic products, and publishes two providers.

## 2. Show the boundaries and publication

On **Dashboard**, walk through the architecture map:

- The Consumer UI discovers service metadata from the Registry.
- The Registry stores metadata and contract references; it does not execute operations.
- The Consumer sends contract-versioned messages through the ESB.
- The ESB validates, routes, applies timeout/correlation policies, and traces outcomes.
- Catalog and Order are separate providers; Catalog and Order publish their metadata to the Registry.

Point out the six lifecycle steps and the current message trace. Then open **Service Registry** and show the two published service descriptors, capabilities, operations, and contract versions. Open the API contract index at `docs/api-contracts.md` or the generated API documentation at <http://127.0.0.1:8000/docs>.

## 3. Place a successful order

Open **Orders**, choose a product, and submit a quantity of `1`.

Expected: the UI returns a confirmed order and displays its order ID and correlation ID. Explain that the Consumer used Registry discovery and sent the request to the Order provider through the ESB; Order checked availability by calling Catalog over HTTP.

Open **Message Trace** (or the Dashboard's latest-message panel). Find the `create-order` trace and match its correlation ID and destination to the response.

## 4. Demonstrate policy and error behavior

Use the UI to request more than the displayed availability. The backend should return a structured `409` conflict; no order should be reported as successful. Refresh the trace view and show the failed outcome.

To demonstrate contract validation, run this from PowerShell while the backend is active:

```powershell
$envelope = @{
    message_id = [guid]::NewGuid().ToString()
    correlation_id = [guid]::NewGuid().ToString()
    service = "order-service"
    operation = "create-order"
    contract_version = "v1"
    payload = @{ items = @(@{ product_id = "book-soa-101"; quantity = 0 }) }
}
$body = $envelope | ConvertTo-Json -Depth 6
try {
    Invoke-RestMethod `
        -Uri http://127.0.0.1:8000/api/esb/dispatch `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
} catch {
    "HTTP status: $($_.Exception.Response.StatusCode.value__)"
    $_.ErrorDetails.Message
}
```

Expected: HTTP 422 with a structured `validation_error` response. The automated ESB tests additionally cover unknown services and operations, unsupported contract versions, provider unavailability, provider timeout, and correlation-aware traces:

```powershell
Set-Location D:\SOA_Order_Management_Starter\soa-order-management\backend
.\.venv\Scripts\python.exe -m pytest tests\test_esb.py tests\test_providers.py -q
```

## 5. Explain the four SOA tenets

- **Explicit boundaries:** Consumer uses public APIs and contracts; provider implementation modules are not imported by the UI.
- **Autonomy:** Catalog and Order own their logic and separate SQLite tables. Order requests availability through Catalog's HTTP contract.
- **Shared contracts, not implementation:** Pydantic contracts define backend interfaces; the React client uses corresponding public TypeScript API types.
- **Policy-driven compatibility:** The ESB enforces contract versions and payload validation, propagates correlation IDs, limits upstream calls with a configured timeout, and returns normalized errors. Provider registration is restricted to local loopback endpoints in this demo.

## Limitations to disclose

- Product availability is checked but not reserved or decremented; repeated orders can exceed the displayed stock.
- Catalog and Order records persist in SQLite. Registry metadata and message traces are in memory and reset on backend restart.
- The registry's registration endpoint is demo-only and has no authentication. Do not expose it beyond trusted local use.
- Payment, shipping, and real customer identity are outside the project scope.

Stop Uvicorn and Vite with `Ctrl+C` in their respective terminals.

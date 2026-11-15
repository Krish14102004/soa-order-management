# Engineering Rules and AI Boundaries

## 1. General Rules
- Implement in small, testable phases. Do not generate the entire application in one unreviewable change.
- Preserve the boundaries documented in `architecture.md`.
- Keep functions and modules focused.
- Prefer readable code over clever abstractions.
- Add or update tests whenever behavior changes.
- Update `memory.md` after each completed task or meaningful milestone.
- Update `phases.md` when a phase changes status.
- Never silently change agreed requirements or architecture.

## 2. Technology Rules
- Backend: Python + FastAPI + Pydantic.
- Frontend: React + TypeScript + Vite.
- Use REST/HTTP for the first version.
- Use SQLite for the initial local prototype.
- Use Pytest for backend tests.
- Avoid adding a library when the standard library or current stack is sufficient.
- Pin or constrain dependencies in the relevant dependency file.
- Do not introduce Kafka, RabbitMQ, Kubernetes, or a commercial ESB unless a requirement justifies the complexity.

## 3. Architecture Boundaries
- Consumer UI communicates through public APIs only.
- Service Registry is responsible for service metadata and discovery only.
- ESB is responsible for routing, mediation, cross-cutting policies, and trace metadata only.
- Catalog Service owns product/catalogue data and availability logic.
- Order Service owns order creation and order status.
- Never place business logic in the frontend, registry, or ESB.
- Never import provider-internal implementation modules into the consumer.
- Contracts must describe externally visible operations and data formats.

## 4. API and Contract Rules
- Validate all external input.
- Use explicit request and response models.
- Version contracts deliberately; do not make breaking changes without documenting them.
- Return consistent error structures with an appropriate HTTP status.
- Do not expose stack traces, secrets, or internal database details to clients.
- Document endpoint purpose and payload examples.
- Include correlation IDs in ESB traces and error logs.

## 5. Error Handling
- Handle validation errors, unknown services, unknown operations, provider unavailability, timeouts, and unexpected failures separately.
- Use meaningful HTTP status codes.
- Log internal diagnostic details server-side.
- Return safe, structured messages to the consumer.
- Do not swallow exceptions or return success-shaped responses for failures.
- Set explicit timeouts for service-to-service HTTP calls.

## 6. Security and Data
- Never collect or store real card numbers, CVVs, passwords, or unnecessary personal information.
- Keep secrets in environment variables; commit only `.env.example`.
- Validate service registration metadata to prevent arbitrary unsafe destinations.
- Restrict registry registration to trusted local/admin setup in the initial version, or clearly document the demo-only limitation.
- Avoid unsafe dynamic imports or arbitrary code execution.
- Do not disable CORS/security checks merely to make an error disappear; configure them narrowly.

## 7. Frontend Rules
- Use TypeScript types for API data.
- Keep API calls in `services/apiClient.ts`, not scattered through components.
- Keep UI components presentational where practical.
- Show loading, empty, success, and error states.
- Do not hardcode service endpoints in multiple components.
- Do not fake a successful service interaction with local UI state.

## 8. Testing Rules
- Test contracts and validation.
- Test registry registration and discovery.
- Test ESB routing and failure cases.
- Test successful and failed order flows.
- Do not claim a test passed unless it was actually run.
- Keep test data synthetic.

## 9. AI Agent Boundaries
The AI agent may:
- Inspect the repository and propose changes.
- Create documentation, code, tests, and configuration.
- Explain trade-offs and identify missing requirements.
- Suggest commands for the developer to run.

The AI agent must not:
- Claim to have installed software, downloaded datasets, started servers, or run tests unless the environment confirms it.
- Invent API keys, credentials, user data, datasets, or external service access.
- Delete or overwrite user work without explicit approval.
- Change the stack or architecture without explaining the reason and requesting approval.
- Add real payment processing or collect sensitive financial information.
- Proceed past a blocker that requires a human decision.

## 10. Human-Required Tasks
If an action requires the developer:
1. Stop at that dependency.
2. Explain exactly why it is needed.
3. Provide the official download or setup page where known.
4. Give numbered, OS-appropriate steps.
5. State the expected file name, folder location, command, or success indicator.
6. Wait for confirmation or the required file before continuing.
Examples: installing Python/Node, creating credentials, downloading a required dataset, configuring environment variables, or granting access.

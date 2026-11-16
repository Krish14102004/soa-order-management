# Product Requirements Document (PRD)
# SOA-Based Distributed Order Management System

## 1. Product Overview
Build an educational, working Service-Oriented Architecture (SOA) demonstration using a mail-order/e-commerce scenario. A customer (Service Consumer) discovers and invokes independently managed business services (Service Providers) through a Service Registry and an ESB/transport layer.

The application must demonstrate real service interactions, not merely present a static architecture diagram.

## 2. Problem Statement
SOA concepts are often taught as separate definitions. This project makes them observable through a functioning order workflow: service publication, discovery, contract-based requests, message routing, processing, and response delivery.

## 3. Target Users
- Students learning Service-Oriented Architecture.
- Faculty evaluating SOA principles and implementation.
- Developers exploring service contracts, discovery, and message mediation.

## 4. Goals
- Demonstrate the provider, consumer, registry, contracts, and transport/ESB roles.
- Implement a complete order placement flow across independently structured services.
- Make service discovery and message routing inspectable through the UI and logs.
- Demonstrate the four SOA tenets with concrete implementation choices.
- Keep the project understandable, locally runnable, and testable.

## 5. Out of Scope
- Real payments or storage of card details.
- Production-grade distributed deployment or cloud hosting.
- Real courier/shipping integration.
- Authentication with real customer identity providers.
- Kubernetes, Kafka, or a full enterprise ESB unless later justified.

## 6. Core Features
### F1. Customer / Service Consumer
- Browse products.
- Add a product and quantity to an order.
- Submit an order using the published contract.
- View order status and response details.
- Review previously saved orders and their items, status, and placement time.

### F2. Service Provider
- Catalog Service: return products and availability.
- Order Service: validate and create orders.
- Each service owns its business logic and exposes documented endpoints.

### F3. Service Registry
- Register service metadata: service name, description, endpoint, operations, contract location, and health/status.
- List registered services.
- Allow the consumer to discover a service by name or capability.
- Do not make the registry responsible for executing business operations.

### F4. Service and Data Contracts
- Define request and response schemas.
- Publish contract metadata with each service.
- Validate incoming requests against typed schemas.
- Return structured validation errors.
- Keep contract/interface definitions separate from service implementation.

### F5. ESB / Transport Layer
- Accept consumer messages through a defined gateway endpoint.
- Resolve the destination service using registered routing metadata.
- Validate or invoke contract validation before forwarding.
- Route requests to the correct provider.
- Record correlation ID, source, destination, status, and timing.
- Return a normalized response to the consumer.
- Do not put order or catalog business logic inside the ESB.

### F6. Observability Dashboard
- Show registered services and their status.
- Show a readable sequence of the six interaction steps.
- Show recent message traffic and routing logs.
- Display correlation IDs and success/failure outcomes.
- Provide a clear architecture view linking consumer, registry, ESB, and providers.

### F7. SOA Tenets
- Explicit Boundaries: public interfaces only; internal implementation stays private.
- Autonomy: services own their logic and data boundaries.
- Shared Contracts, Not Implementation: consumer and provider depend on schemas/interfaces, not shared internal code.
- Policy-Driven Compatibility: document and enforce policies such as accepted content type, schema version, timeout, and authorization requirements where implemented.

## 7. Six-Step Lifecycle
1. Service Setup: provider initializes and exposes its service.
2. Publishing Registry: provider registers metadata and contract information.
3. Discovery: consumer queries the registry.
4. Contract Agreement: consumer prepares a payload matching the service/data contract.
5. Message Dispatch: consumer sends the request through the ESB/transport.
6. Delivery & Response: provider executes business logic and the response returns to the consumer.

## 8. Functional Requirements
- FR-01: The application shall list all registered services.
- FR-02: A provider shall be able to register its service metadata.
- FR-03: The consumer shall discover the Order and Catalog services.
- FR-04: The application shall expose request and response contracts.
- FR-05: Invalid request payloads shall be rejected with useful validation details.
- FR-06: The consumer shall submit an order through the ESB.
- FR-07: The Order Service shall check product availability through the Catalog Service or a clearly documented service boundary.
- FR-08: Successful orders shall receive a unique order ID and status.
- FR-09: The ESB shall record a correlation ID and routing result.
- FR-10: The UI shall display the lifecycle and message trace.
- FR-11: Service failures shall produce structured error responses.
- FR-12: Automated tests shall cover contracts, services, registry, and end-to-end order flow.
- FR-13: The consumer shall retrieve and display persisted order history through the Order Service contract and ESB.

## 9. Non-Functional Requirements
- Maintain clear separation between consumer, registry, ESB, and providers.
- Use explicit API contracts and predictable error formats.
- Keep local setup simple and document all commands.
- Avoid storing sensitive payment data.
- Provide readable logs and testable components.
- Use environment variables for configurable URLs and ports.
- Ensure services can be tested independently.

## 10. Acceptance Criteria
- A user can browse products and place an order from the UI.
- The consumer discovers services from the registry rather than hardcoding all provider endpoints.
- The order request follows a documented schema.
- The ESB visibly routes the request to the Order Service.
- The order result is returned and displayed.
- A trace/log makes the lifecycle understandable.
- Invalid data and unavailable services are handled without an unhandled crash.
- Tests pass and setup instructions work from a clean checkout.

## 11. Assumptions / Decisions to Confirm
- Initial implementation is local and educational.
- SQLite is sufficient for the first working version.
- REST/HTTP is the transport for the initial version.
- The ESB is a lightweight custom mediation/routing component, not a commercial ESB product.
- No real payment gateway is required.

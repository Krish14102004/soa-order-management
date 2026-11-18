# UI Design System

## 1. Design Direction
A clean, modern technical operations dashboard. It should feel like a polished developer tool, not a generic shopping template. The e-commerce scenario is the teaching example; the SOA architecture is the main subject.

## 2. Theme
- Default: light theme, with a persistent user-selectable dark theme.
- Dark theme: deep navy page background (`#0D111B`), charcoal surfaces (`#171E2B`), pale text (`#E8ECF4`), muted slate labels, and lightened indigo/teal accents. Preserve clear status colors and contrast in both themes.
- Background: soft cool gray (`#F5F7FA`).
- Surface/cards: white (`#FFFFFF`).
- Primary: deep indigo (`#3446A5`).
- Secondary: blue (`#3977D5`).
- Accent: teal (`#0F9D91`).
- Text: near-black navy (`#172033`).
- Muted text: slate (`#64748B`).
- Border: pale slate (`#E2E8F0`).
- Success: green (`#16845B`).
- Warning: amber (`#B7791F`).
- Error: red (`#C2414B`).

Use color consistently and never rely on color alone to communicate status. Place the theme toggle in the top bar and provide an accessible name describing the destination theme.

## 3. Typography
- Font family: Inter, with system sans-serif fallback.
- Headings: 600–700 weight.
- Body: 400–500 weight.
- Labels and metadata: 500–600 weight.
- Use a clear hierarchy: page title, section title, card title, body, metadata.
- Keep code, IDs, endpoints, and correlation IDs in a monospace font such as JetBrains Mono.

## 4. Layout
- Desktop-first dashboard with responsive behavior for tablet and mobile.
- Left navigation/sidebar for Dashboard, Service Registry, Orders, and Message Trace.
- Top header with project title and backend/connection status.
- Main content uses a consistent grid and generous whitespace.
- Cards have subtle borders, restrained shadows, and consistent radius.
- Avoid excessive gradients, glassmorphism, decorative animation, and crowded panels.

## 5. Key Visual Components
- Architecture map: Consumer → Registry (discovery) and Consumer → ESB → Provider; show provider-to-registry publishing separately.
- Service cards: service name, role, endpoint, status, contract version.
- Lifecycle timeline: six ordered steps with current/completed/failed state.
- Message trace: timestamp, correlation ID, source, destination, operation, status, duration.
- Order form: concise product selector, quantity, and confirmation.
- Tenet cards: principle, implementation evidence, and relevant component.

## 6. Interaction States
Every data-driven view must include loading, empty, error, and populated states.
Use restrained transitions for navigation and routine state changes. Theme changes are the deliberate exception: the outgoing page itself separates into irregular, randomly arranged fragments, beginning near the top-left and falling away over 4–5 seconds to reveal the destination theme directly beneath it. Do not cover the page with an intermediate surface or regular grid. Use the same pacing in both directions. A second activation during the reveal accelerates it to completion instead of reversing it. Respect `prefers-reduced-motion` by switching themes without the fracture animation.

## 7. Accessibility
- Maintain readable contrast.
- Provide visible keyboard focus.
- Use semantic HTML and accessible labels.
- Do not encode meaning using color alone.
- Ensure responsive layouts do not hide critical trace or contract information.

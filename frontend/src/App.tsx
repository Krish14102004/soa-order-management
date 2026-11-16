import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  Check,
  CircleAlert,
  Clock3,
  History,
  Package,
  RefreshCw,
  ShoppingBasket,
  Store,
  Trash2,
  Workflow,
} from 'lucide-react';

import {
  ApiClientError,
  createOrder,
  discoverServices,
  getServices,
  getTraces,
  listOrders,
  listProducts,
} from './services/apiClient';
import type {
  DispatchResponse,
  MessageTrace,
  Order,
  Product,
  ServiceDescriptor,
} from './types/api';

type Page = 'dashboard' | 'registry' | 'orders' | 'history' | 'traces';
type Cart = Record<string, number>;

const navigation: Array<{ id: Page; label: string; icon: typeof Activity }> = [
  { id: 'dashboard', label: 'Dashboard', icon: Workflow },
  { id: 'registry', label: 'Service Registry', icon: Boxes },
  { id: 'orders', label: 'Orders', icon: ShoppingBasket },
  { id: 'history', label: 'Order History', icon: History },
  { id: 'traces', label: 'Message Trace', icon: Activity },
];

const titles: Record<Page, { eyebrow: string; heading: string; description: string }> = {
  dashboard: {
    eyebrow: 'SYSTEM OVERVIEW',
    heading: 'SOA operations at a glance',
    description: 'Follow service publication, discovery, dispatch, and response across the order flow.',
  },
  registry: {
    eyebrow: 'SERVICE DIRECTORY',
    heading: 'Discover published services',
    description: 'The registry describes provider capabilities and contracts. It does not execute business operations.',
  },
  orders: {
    eyebrow: 'CUSTOMER CONSUMER',
    heading: 'Create an order',
    description: 'Choose catalog items, agree to the v1 contract, and send the request through the ESB.',
  },
  history: {
    eyebrow: 'ORDER RECORDS',
    heading: 'Order history',
    description: 'Review saved orders returned by the Order Service through its published contract.',
  },
  traces: {
    eyebrow: 'MESSAGE OBSERVABILITY',
    heading: 'Routing trace',
    description: 'Inspect correlation IDs, destinations, outcomes, and response times from real gateway calls.',
  },
};

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'An unexpected error occurred.';
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function shortId(value: string): string {
  return `${value.slice(0, 8)}…${value.slice(-4)}`;
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value));
}

function serviceRole(service: ServiceDescriptor): string {
  return service.capabilities.includes('catalog')
    ? 'Catalog provider'
    : service.capabilities.includes('orders')
      ? 'Order provider'
      : 'Service provider';
}

function ServiceCard({ service }: { service: ServiceDescriptor }) {
  return (
    <article className="service-card">
      <div className="service-card-top">
        <div className="service-icon"><Store size={18} aria-hidden="true" /></div>
        <span className="health-chip"><span /> Health {service.status}</span>
      </div>
      <p className="eyebrow">{serviceRole(service)}</p>
      <h3>{service.service_name}</h3>
      <p className="muted">{service.description}</p>
      <div className="service-endpoint">
        <span>Endpoint</span>
        <code>{service.endpoint}</code>
      </div>
      <div className="capabilities">
        {service.capabilities.map((capability) => (
          <span className="capability" key={capability}>{capability}</span>
        ))}
        <span className="capability version">v1 contract</span>
      </div>
      <details className="operation-details">
        <summary>{service.operations.length} published operations</summary>
        <ul>
          {service.operations.map((operation) => (
            <li key={operation.name}>
              <code>{operation.method}</code>
              <span>{operation.name}</span>
              <small>{operation.path}</small>
            </li>
          ))}
        </ul>
      </details>
    </article>
  );
}

function TraceTable({ traces }: { traces: MessageTrace[] }) {
  if (!traces.length) {
    return (
      <div className="empty-state">
        <Activity size={22} aria-hidden="true" />
        <strong>No messages yet</strong>
        <span>Dispatch a catalog or order request to see its trace here.</span>
      </div>
    );
  }
  return (
    <div className="table-scroll">
      <table className="trace-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Operation</th>
            <th>Destination</th>
            <th>Correlation ID</th>
            <th>Result</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {traces.map((trace) => (
            <tr key={trace.message_id}>
              <td className="mono">{formatTime(trace.timestamp)}</td>
              <td>{trace.operation}</td>
              <td>{trace.destination}</td>
              <td><code title={trace.correlation_id}>{shortId(trace.correlation_id)}</code></td>
              <td>
                <span className={`result-chip ${trace.status === 'success' ? 'success' : 'failure'}`}>
                  {trace.status === 'success' ? <Check size={13} /> : <CircleAlert size={13} />}
                  {trace.status} · {trace.status_code}
                </span>
              </td>
              <td>{trace.duration_ms.toFixed(1)} ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ArchitectureMap() {
  return (
    <div className="architecture-map" aria-label="Consumer discovers providers and sends requests through the ESB">
      <div className="architecture-node consumer-node">
        <div className="node-symbol"><ShoppingBasket size={19} aria-hidden="true" /></div>
        <strong>Consumer UI</strong>
        <span>Customer application</span>
      </div>
      <div className="architecture-links">
        <div className="link-row discovery-link">
          <span>service discovery</span><ArrowUpRight size={17} aria-hidden="true" />
        </div>
        <div className="link-row dispatch-link">
          <span>contract message</span><ArrowRight size={17} aria-hidden="true" />
        </div>
      </div>
      <div className="architecture-middle">
        <div className="architecture-node registry-node">
          <div className="node-symbol"><Boxes size={18} aria-hidden="true" /></div>
          <strong>Registry</strong>
          <span>Metadata only</span>
        </div>
        <div className="architecture-node esb-node">
          <div className="node-symbol"><Workflow size={18} aria-hidden="true" /></div>
          <strong>ESB / Gateway</strong>
          <span>Validate · route · trace</span>
        </div>
      </div>
      <div className="architecture-links provider-links">
        <div className="link-row"><span>routed HTTP</span><ArrowRight size={17} aria-hidden="true" /></div>
      </div>
      <div className="architecture-providers">
        <div className="architecture-node provider-node">
          <div className="node-symbol"><Package size={18} aria-hidden="true" /></div>
          <strong>Catalog</strong>
          <span>Products · availability</span>
        </div>
        <div className="architecture-node provider-node">
          <div className="node-symbol"><Store size={18} aria-hidden="true" /></div>
          <strong>Order</strong>
          <span>Create · history</span>
        </div>
      </div>
      <div className="provider-publish">
        <ArrowUpRight size={15} aria-hidden="true" />
        <strong>Provider publication</strong>
        <span>Catalog &amp; Order publish metadata and contracts to the Registry</span>
      </div>
    </div>
  );
}

function Lifecycle({
  hasServices,
  latestTrace,
}: {
  hasServices: boolean;
  latestTrace: MessageTrace | undefined;
}) {
  const steps = [
    { title: 'Service setup', state: hasServices ? 'Complete' : 'Waiting' },
    { title: 'Registry publish', state: hasServices ? 'Complete' : 'Waiting' },
    { title: 'Consumer discovery', state: hasServices ? 'Complete' : 'Waiting' },
    { title: 'Contract agreement', state: hasServices ? 'Ready · v1' : 'Waiting' },
    {
      title: 'Message dispatch',
      state: latestTrace ? (latestTrace.status === 'success' ? 'Complete' : 'Failed') : 'Ready',
    },
    {
      title: 'Delivery & response',
      state: latestTrace ? (latestTrace.status === 'success' ? 'Complete' : 'Failed') : 'Waiting',
    },
  ];
  return (
    <ol className="lifecycle">
      {steps.map((step, index) => (
        <li
          className={
            step.state === 'Complete' || step.state === 'Ready · v1'
              ? 'done'
              : step.state === 'Failed'
                ? 'failed'
                : ''
          }
          key={step.title}
        >
          <span className="step-number">{index + 1}</span>
          <div><strong>{step.title}</strong><small>{step.state}</small></div>
        </li>
      ))}
    </ol>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [services, setServices] = useState<ServiceDescriptor[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [traces, setTraces] = useState<MessageTrace[]>([]);
  const [cart, setCart] = useState<Cart>({});
  const [lastOrder, setLastOrder] = useState<DispatchResponse<Order> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const [orderError, setOrderError] = useState('');
  const [orderBusy, setOrderBusy] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking');

  const refresh = useCallback(async (background = false) => {
    if (background) setRefreshing(true);
    else setLoading(true);
    setConnectionError('');
    try {
      const [registered, recentTraces, catalogProviders] = await Promise.all([
        getServices(),
        getTraces(),
        discoverServices('catalog'),
      ]);
      setServices(registered);
      setTraces(recentTraces);
      setHealth('online');
      const catalog = catalogProviders[0];
      if (catalog) {
        const result = await listProducts(catalog);
        setProducts(result.payload.products);
        setTraces(await getTraces());
      } else {
        setProducts([]);
      }
    } catch (error) {
      setHealth('offline');
      setConnectionError(getErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const loadOrderHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError('');
    try {
      const discovered = await discoverServices('orders');
      const orderService = discovered.find((service) =>
        service.operations.some((operation) => operation.name === 'list-orders'),
      );
      if (!orderService) {
        throw new ApiClientError(
          'No discovered Order service publishes list-orders.',
          404,
          'order_history_unavailable',
          null,
        );
      }
      const result = await listOrders(orderService);
      setOrders(result.payload.orders);
    } catch (error) {
      setHistoryError(getErrorMessage(error));
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (page === 'history') void loadOrderHistory();
  }, [page, loadOrderHistory]);

  const pageInfo = titles[page];
  const selectedCount = Object.keys(cart).length;
  const catalogCount = services.filter((service) => service.capabilities.includes('catalog')).length;
  const orderCount = services.filter((service) => service.capabilities.includes('orders')).length;
  const latestTrace = traces[0];
  const cartItems = useMemo(
    () => products.filter((product) => cart[product.product_id]),
    [cart, products],
  );

  const addToCart = (productId: string, quantity: number) => {
    setOrderError('');
    setCart((current) => ({ ...current, [productId]: (current[productId] ?? 0) + quantity }));
  };

  const updateCartQuantity = (productId: string, quantity: number) => {
    setCart((current) => {
      const next = { ...current };
      if (quantity <= 0) delete next[productId];
      else next[productId] = quantity;
      return next;
    });
  };

  const submitOrder = async () => {
    setOrderError('');
    setLastOrder(null);
    setOrderBusy(true);
    try {
      const discovered = await discoverServices('orders');
      const orderService = discovered.find((service) =>
        service.operations.some((operation) => operation.name === 'create-order'),
      );
      if (!orderService) {
        throw new ApiClientError(
          'No discovered Order service publishes create-order.',
          404,
          'order_service_not_found',
          null,
        );
      }
      const result = await createOrder(
        orderService,
        Object.entries(cart).map(([product_id, quantity]) => ({ product_id, quantity })),
      );
      setLastOrder(result);
      setCart({});
      await refresh(true);
      await loadOrderHistory();
    } catch (error) {
      setOrderError(getErrorMessage(error));
      try {
        setTraces(await getTraces());
      } catch {
        setConnectionError('The request failed and the latest trace could not be loaded.');
      }
    } finally {
      setOrderBusy(false);
    }
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage('dashboard'); }}>
          <span className="brand-mark"><Workflow size={20} aria-hidden="true" /></span>
          <span><strong>SOA Studio</strong><small>ORDER MANAGEMENT</small></span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          {navigation.map(({ id, label, icon: Icon }) => (
            <button
              aria-label={label}
              aria-current={page === id ? 'page' : undefined}
              className={`nav-item ${page === id ? 'active' : ''}`}
              key={id}
              onClick={() => setPage(id)}
              type="button"
            >
              <Icon size={17} aria-hidden="true" />
              <span>{label}</span>
              {id === 'orders' && selectedCount > 0 && <span className="nav-count">{selectedCount}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-icon"><ArrowDownLeft size={15} aria-hidden="true" /></span>
            <strong>Built to explore SOA</strong>
            <p>Separate boundaries. Shared contracts. Observable messages.</p>
          </div>
          <span className="sidebar-version">LOCAL DEMO <span>v0.1.0</span></span>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">SOA ORDER MANAGEMENT <span>/</span> {pageInfo.eyebrow}</div>
          <div className={`connection-pill ${health}`}>
            <span className="connection-dot" />
            {health === 'online' ? 'Backend connected' : health === 'offline' ? 'Backend unavailable' : 'Connecting'}
          </div>
        </header>
        <div className="content-wrap">
          <div className="page-heading">
            <div>
              <p className="eyebrow">{pageInfo.eyebrow}</p>
              <h1>{pageInfo.heading}</h1>
              <p className="page-description">{pageInfo.description}</p>
            </div>
            <button className="button button-secondary refresh-button" onClick={() => void refresh(true)} disabled={refreshing} type="button">
              <RefreshCw size={15} className={refreshing ? 'spin' : ''} aria-hidden="true" />
              Refresh
            </button>
          </div>

          {connectionError && (
            <div className="alert alert-error" role="alert">
              <CircleAlert size={18} aria-hidden="true" />
              <div><strong>Could not load live service data</strong><p>{connectionError}</p></div>
              <button className="text-button" onClick={() => void refresh()} type="button">Try again</button>
            </div>
          )}

          {loading ? (
            <div className="loading-panel" role="status"><span className="spinner" />Connecting to the SOA services…</div>
          ) : page === 'dashboard' ? (
            <Dashboard
              catalogCount={catalogCount}
              latestTrace={latestTrace}
              onNavigate={setPage}
              orderCount={orderCount}
              services={services}
              traces={traces}
            />
          ) : page === 'registry' ? (
            <RegistryPage services={services} />
          ) : page === 'orders' ? (
            <OrdersPage
              busy={orderBusy}
              cart={cart}
              cartItems={cartItems}
              error={orderError}
              lastOrder={lastOrder}
              onAdd={addToCart}
              onPlaceOrder={() => void submitOrder()}
              onQuantityChange={updateCartQuantity}
              products={products}
            />
          ) : page === 'history' ? (
            <OrderHistoryPage
              error={historyError}
              loading={historyLoading}
              onRefresh={() => void loadOrderHistory()}
              orders={orders}
            />
          ) : (
            <TracesPage traces={traces} />
          )}

          <footer className="page-footer">
            <span>SOA-Based Distributed Order Management System</span>
            <span>REST · Contracts v1 · Local environment</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function Dashboard({
  catalogCount,
  latestTrace,
  onNavigate,
  orderCount,
  services,
  traces,
}: {
  catalogCount: number;
  latestTrace: MessageTrace | undefined;
  onNavigate: (page: Page) => void;
  orderCount: number;
  services: ServiceDescriptor[];
  traces: MessageTrace[];
}) {
  return (
    <>
      <section className="metrics-grid" aria-label="System summary">
        <Metric icon={Boxes} label="Published services" value={services.length} detail="Discovered from registry" />
        <Metric icon={Package} label="Catalog provider" value={catalogCount ? 'Published' : '—'} detail="Discovered from registry" />
        <Metric icon={Store} label="Order provider" value={orderCount ? 'Published' : '—'} detail="Discovered from registry" />
        <Metric icon={Activity} label="Recent messages" value={traces.length} detail="Latest gateway traces" />
      </section>

      <section className="panel architecture-panel">
        <div className="section-heading">
          <div><p className="eyebrow">SERVICE LANDSCAPE</p><h2>One request, clear boundaries</h2></div>
          <span className="live-label"><span /> LIVE ARCHITECTURE</span>
        </div>
        <ArchitectureMap />
      </section>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="section-heading compact">
            <div><p className="eyebrow">INTERACTION LIFECYCLE</p><h2>Six steps of a service call</h2></div>
          </div>
          <Lifecycle hasServices={services.length > 0} latestTrace={latestTrace} />
        </section>
        <section className="panel recent-panel">
          <div className="section-heading compact">
            <div><p className="eyebrow">LATEST MESSAGE</p><h2>Gateway activity</h2></div>
            <button className="text-button" onClick={() => onNavigate('traces')} type="button">View all</button>
          </div>
          {latestTrace ? (
            <div className="latest-trace">
              <div className={`trace-status-icon ${latestTrace.status === 'success' ? 'success' : 'failure'}`}>
                {latestTrace.status === 'success' ? <Check size={17} /> : <CircleAlert size={17} />}
              </div>
              <div className="latest-trace-copy">
                <strong>{latestTrace.operation}</strong>
                <span>{latestTrace.destination}</span>
                <code title={latestTrace.correlation_id}>corr · {shortId(latestTrace.correlation_id)}</code>
              </div>
              <span className="trace-duration">{latestTrace.duration_ms.toFixed(1)} ms</span>
            </div>
          ) : (
            <div className="compact-empty">No gateway messages have been recorded yet.</div>
          )}
          <div className="tenet-callout">
            <span>SOA TENET</span>
            <p>Consumers depend on published contracts—not provider implementation details.</p>
          </div>
        </section>
      </div>

      <section className="panel service-overview">
        <div className="section-heading">
          <div><p className="eyebrow">SERVICE REGISTRY</p><h2>Published providers</h2></div>
          <button className="text-button" onClick={() => onNavigate('registry')} type="button">Open registry <ArrowUpRight size={14} /></button>
        </div>
        {services.length ? (
          <div className="service-mini-grid">
            {services.map((service) => (
              <div className="service-mini" key={service.service_name}>
                <span className="mini-icon"><Store size={16} /></span>
                <div><strong>{service.service_name}</strong><span>{service.capabilities.join(' · ')}</span></div>
                <span className="mini-status">Published</span>
              </div>
            ))}
          </div>
        ) : <div className="compact-empty">No services are registered.</div>}
      </section>
    </>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  detail: string;
}) {
  return (
    <article className="metric-card">
      <div className="metric-top"><span>{label}</span><Icon size={17} aria-hidden="true" /></div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function RegistryPage({ services }: { services: ServiceDescriptor[] }) {
  return (
    <section className="registry-content">
      <div className="registry-summary">
        <div><strong>{services.length}</strong><span>services in directory</span></div>
        <p>Provider metadata is published at startup. The registry stores endpoint and contract references only.</p>
      </div>
      {services.length ? (
        <div className="service-card-grid">
          {services.map((service) => <ServiceCard key={service.service_name} service={service} />)}
        </div>
      ) : (
        <div className="empty-state panel">
          <Boxes size={24} aria-hidden="true" />
          <strong>Registry is empty</strong>
          <span>Start the backend to publish the Catalog and Order services.</span>
        </div>
      )}
      <div className="info-strip"><CircleAlert size={16} /><span>Registration is an unauthenticated, local-demo operation. Do not expose this registry to untrusted networks.</span></div>
    </section>
  );
}

function OrdersPage({
  busy,
  cart,
  cartItems,
  error,
  lastOrder,
  onAdd,
  onPlaceOrder,
  onQuantityChange,
  products,
}: {
  busy: boolean;
  cart: Cart;
  cartItems: Product[];
  error: string;
  lastOrder: DispatchResponse<Order> | null;
  onAdd: (productId: string, quantity: number) => void;
  onPlaceOrder: () => void;
  onQuantityChange: (productId: string, quantity: number) => void;
  products: Product[];
}) {
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  return (
    <div className="orders-layout">
      <section className="panel products-panel">
        <div className="section-heading">
          <div><p className="eyebrow">CATALOG SERVICE · DISCOVERED</p><h2>Available products</h2></div>
          <span className="contract-pill">ProductList v1</span>
        </div>
        {!products.length ? (
          <div className="empty-state">
            <Package size={23} aria-hidden="true" />
            <strong>No products available</strong>
            <span>Product data is loaded through the discovered Catalog service and ESB.</span>
          </div>
        ) : (
          <div className="product-list">
            {products.map((product) => {
              const quantity = quantities[product.product_id] ?? 1;
              return (
                <article className="product-row" key={product.product_id}>
                  <div className="product-art"><Package size={20} aria-hidden="true" /></div>
                  <div className="product-copy">
                    <span className="product-id">{product.product_id}</span>
                    <h3>{product.name}</h3>
                    <p>{product.description}</p>
                    <span className="stock-label">{product.available_quantity} units reported available</span>
                  </div>
                  <div className="product-actions">
                    <label className="sr-only" htmlFor={`quantity-${product.product_id}`}>Quantity for {product.name}</label>
                    <input
                      id={`quantity-${product.product_id}`}
                      min="1"
                      onChange={(event) => setQuantities((current) => ({
                        ...current,
                        [product.product_id]: Math.max(1, Number(event.target.value) || 1),
                      }))}
                      type="number"
                      value={quantity}
                    />
                    <button className="button button-primary" onClick={() => onAdd(product.product_id, quantity)} type="button">
                      Add to order
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <aside className="panel cart-panel">
        <div className="section-heading compact">
          <div><p className="eyebrow">ORDER CONTRACT · v1</p><h2>Your order</h2></div>
          <span className="cart-count">{cartItems.length}</span>
        </div>
        {!cartItems.length ? (
          <div className="cart-empty"><ShoppingBasket size={23} /><span>Add products to prepare a request.</span></div>
        ) : (
          <div className="cart-items">
            {cartItems.map((product) => (
              <div className="cart-item" key={product.product_id}>
                <div><strong>{product.name}</strong><code>{product.product_id}</code></div>
                <label className="sr-only" htmlFor={`cart-${product.product_id}`}>Order quantity for {product.name}</label>
                <input
                  id={`cart-${product.product_id}`}
                  min="0"
                  onChange={(event) => onQuantityChange(product.product_id, Number(event.target.value))}
                  type="number"
                  value={cart[product.product_id]}
                />
                <button aria-label={`Remove ${product.name}`} className="icon-button" onClick={() => onQuantityChange(product.product_id, 0)} type="button">
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
        {error && <div className="inline-error" role="alert"><CircleAlert size={15} />{error}</div>}
        <button
          className="button button-primary place-order"
          disabled={!cartItems.length || busy}
          onClick={onPlaceOrder}
          type="button"
        >
          {busy ? <><span className="button-spinner" /> Dispatching through ESB…</> : <>Place order <ArrowRight size={16} /></>}
        </button>
        <div className="order-flow-note">
          <Workflow size={16} />
          <span>Consumer → Registry discovery → ESB → Order Service → Catalog availability</span>
        </div>
        {lastOrder && (
          <div className="order-success" role="status">
            <div className="success-heading"><Check size={17} /><strong>Order confirmed</strong></div>
            <span>Order ID</span><code>{lastOrder.payload.order_id}</code>
            <span>Correlation ID</span><code>{lastOrder.correlation_id}</code>
            <span>Status</span><strong className="confirmed-status">{lastOrder.payload.status}</strong>
          </div>
        )}
      </aside>
    </div>
  );
}

function OrderHistoryPage({
  error,
  loading,
  onRefresh,
  orders,
}: {
  error: string;
  loading: boolean;
  onRefresh: () => void;
  orders: Order[];
}) {
  return (
    <section className="panel order-history-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ORDER SERVICE · DISCOVERED</p>
          <h2>Saved orders</h2>
        </div>
        <button
          className="button button-secondary"
          disabled={loading}
          onClick={onRefresh}
          type="button"
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} aria-hidden="true" />
          Refresh history
        </button>
      </div>
      {error && (
        <div className="alert alert-error" role="alert">
          <CircleAlert size={16} aria-hidden="true" />
          <div><strong>Could not load order history</strong><p>{error}</p></div>
        </div>
      )}
      {loading && !orders.length ? (
        <div className="loading-panel" role="status"><span className="spinner" />Loading saved orders…</div>
      ) : orders.length ? (
        <div className="table-scroll">
          <table className="trace-table order-history-table">
            <thead>
              <tr>
                <th>Placed</th>
                <th>Order ID</th>
                <th>Items</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.order_id}>
                  <td>{formatDateTime(order.created_at)}</td>
                  <td><code title={order.order_id}>{order.order_id}</code></td>
                  <td>
                    <ul className="order-history-items">
                      {order.items.map((item, index) => (
                        <li key={`${item.product_id}-${index}`}>
                          <span>{item.product_id}</span>
                          <span>× {item.quantity}</span>
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td><span className={`order-status ${order.status}`}>{order.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !error ? (
        <div className="empty-state">
          <History size={23} aria-hidden="true" />
          <strong>{loading ? 'Loading order history' : 'No orders yet'}</strong>
          <span>
            {loading
              ? 'The Order Service is returning saved orders.'
              : 'Orders confirmed by the Order Service will appear here.'}
          </span>
        </div>
      ) : null}
      <div className="info-strip">
        <History size={16} aria-hidden="true" />
        <span>History is loaded from the Order Service and persisted in its SQLite-owned order table.</span>
      </div>
    </section>
  );
}

function TracesPage({ traces }: { traces: MessageTrace[] }) {
  return (
    <>
      <section className="metrics-grid trace-metrics">
        <Metric icon={Activity} label="Recorded messages" value={traces.length} detail="Recent gateway requests" />
        <Metric icon={Check} label="Successful" value={traces.filter((trace) => trace.status === 'success').length} detail="Provider responses returned" />
        <Metric icon={CircleAlert} label="Failed" value={traces.filter((trace) => trace.status !== 'success').length} detail="Normalized error outcomes" />
        <Metric icon={Clock3} label="Trace capacity" value="200" detail="Newest messages retained" />
      </section>
      <section className="panel trace-panel">
        <div className="section-heading">
          <div><p className="eyebrow">ESB / GATEWAY</p><h2>Recent message traffic</h2></div>
          <span className="contract-pill">Correlation-aware</span>
        </div>
        <TraceTable traces={traces} />
      </section>
      <div className="info-strip"><Activity size={16} /><span>Trace history is held in memory and clears when the backend restarts.</span></div>
    </>
  );
}

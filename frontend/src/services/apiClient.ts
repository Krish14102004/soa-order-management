import type {
  ApiErrorResponse,
  DispatchResponse,
  MessageTrace,
  Order,
  ProductList,
  ServiceDescriptor,
} from '../types/api';

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
).replace(/\/+$/, '');

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly correlationId: string | null;

  constructor(
    message: string,
    status: number,
    code: string,
    correlationId: string | null,
  ) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
      signal: AbortSignal.timeout(8000),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new ApiClientError(
        'The backend did not respond within 8 seconds.',
        0,
        'request_timeout',
        null,
      );
    }
    throw new ApiClientError(
      'Cannot connect to the backend. Check that the API server is running.',
      0,
      'backend_unavailable',
      null,
    );
  }

  if (!response.ok) {
    let apiError: ApiErrorResponse | undefined;
    try {
      apiError = (await response.json()) as ApiErrorResponse;
    } catch {
      apiError = undefined;
    }
    throw new ApiClientError(
      apiError?.error?.message ?? `The backend returned HTTP ${response.status}.`,
      response.status,
      apiError?.error?.code ?? 'http_error',
      apiError?.correlation_id ?? response.headers.get('X-Correlation-ID'),
    );
  }

  return (await response.json()) as T;
}

export function getServices(): Promise<ServiceDescriptor[]> {
  return request('/api/registry/services');
}

export function discoverServices(capability: string): Promise<ServiceDescriptor[]> {
  return request(`/api/registry/discover?capability=${encodeURIComponent(capability)}`);
}

export function getTraces(): Promise<MessageTrace[]> {
  return request('/api/esb/traces?limit=50');
}

export function listProducts(
  service: ServiceDescriptor,
): Promise<DispatchResponse<ProductList>> {
  const operation = service.operations.find((candidate) => candidate.name === 'list-products');
  if (!operation) {
    throw new ApiClientError(
      'The discovered Catalog service does not publish list-products.',
      422,
      'missing_operation',
      null,
    );
  }
  return dispatch(service.service_name, operation.name, {});
}

export function createOrder(
  service: ServiceDescriptor,
  items: Array<{ product_id: string; quantity: number }>,
): Promise<DispatchResponse<Order>> {
  const operation = service.operations.find((candidate) => candidate.name === 'create-order');
  if (!operation) {
    throw new ApiClientError(
      'The discovered Order service does not publish create-order.',
      422,
      'missing_operation',
      null,
    );
  }
  return dispatch(service.service_name, operation.name, { items });
}

function dispatch<T>(
  service: string,
  operation: string,
  payload: unknown,
): Promise<DispatchResponse<T>> {
  return request('/api/esb/dispatch', {
    method: 'POST',
    body: JSON.stringify({
      message_id: crypto.randomUUID(),
      correlation_id: crypto.randomUUID(),
      service,
      operation,
      contract_version: 'v1',
      payload,
    }),
  });
}

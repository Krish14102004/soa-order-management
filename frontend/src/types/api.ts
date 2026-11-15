export type ServiceHealth = 'unknown' | 'healthy' | 'unhealthy';

export interface ServiceOperation {
  name: string;
  method: 'GET' | 'POST';
  path: string;
  contract_version: string;
}

export interface ServiceDescriptor {
  service_name: string;
  description: string;
  endpoint: string;
  capabilities: string[];
  contract_url: string;
  operations: ServiceOperation[];
  status: ServiceHealth;
  registered_at: string;
}

export interface Product {
  product_id: string;
  name: string;
  description: string | null;
  available_quantity: number;
}

export interface ProductList {
  products: Product[];
}

export interface OrderItem {
  product_id: string;
  quantity: number;
}

export interface Order {
  order_id: string;
  status: 'pending' | 'confirmed' | 'rejected';
  items: OrderItem[];
  created_at: string;
}

export interface DispatchResponse<T> {
  message_id: string;
  correlation_id: string;
  service: string;
  operation: string;
  status_code: number;
  payload: T;
}

export interface MessageTrace {
  message_id: string;
  correlation_id: string;
  timestamp: string;
  source: string;
  destination: string;
  operation: string;
  status: string;
  status_code: number;
  duration_ms: number;
}

export interface ApiErrorBody {
  code: string;
  message: string;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
  details: Array<{
    location: Array<string | number>;
    message: string;
    code: string;
  }>;
  correlation_id: string | null;
}

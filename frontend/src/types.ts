export type User = {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role_id: number;
  role_code: string;
  role_name: string;
  is_active: boolean;
  permissions: string[];
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type Role = {
  id: number;
  code: string;
  name: string;
  description: string;
  permissions: { id: number; code: string; name: string; module: string; description: string }[];
};

export type Customer = {
  id: number;
  identification: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  is_active: boolean;
};

export type Category = { id: number; name: string; description: string };

export type Product = {
  id: number;
  sku: string;
  name: string;
  description: string;
  category_id: number;
  category_name: string;
  sale_price: number;
  cost: number;
  is_active: boolean;
  quantity: number;
  reorder_level: number;
};

export type Movement = {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  movement_type: string;
  quantity: number;
  previous_quantity: number;
  new_quantity: number;
  reference_type: string;
  reference_id: number | null;
  notes: string;
  user_name: string | null;
  created_at: string;
};

export type SaleDetail = {
  id: number;
  product_id: number;
  sku: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
};

export type Sale = {
  id: number;
  number: string;
  customer_id: number;
  customer_name: string;
  user_id: number;
  user_name: string;
  status: string;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  sale_date: string;
  notes: string;
  details: SaleDetail[];
};

export type Dashboard = {
  total_ventas: number;
  cantidad_ventas: number;
  productos: number;
  clientes: number;
  bajo_inventario: number;
  ventas_por_mes: { mes: string; cantidad: number; importe: number }[];
  productos_mas_vendidos: { producto: string; sku: string; unidades: number; importe: number }[];
  vendedores: { vendedor: string; usuario: string; cantidad: number; importe: number }[] | null;
  alcance: string;
};

export type AssistantAction = {
  type: string;
  label: string;
  route?: string | null;
  confirmation_token?: string | null;
};

export type AssistantSource = { title: string; excerpt: string };

export type AssistantReply = {
  message: string;
  intent: string;
  sources: AssistantSource[];
  actions: AssistantAction[];
  data: Record<string, unknown> | null;
  available: boolean;
};

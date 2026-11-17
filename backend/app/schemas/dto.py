from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)


class UserOut(OrmModel):
    id: int
    username: str
    email: str
    full_name: str
    role_id: int
    role_code: str
    role_name: str
    is_active: bool
    permissions: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=120)
    full_name: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=100)
    role_id: int
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    full_name: str = Field(min_length=3, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=100)
    role_id: int
    is_active: bool = True


class StatusUpdate(BaseModel):
    is_active: bool


class PermissionOut(OrmModel):
    id: int
    code: str
    name: str
    module: str
    description: str


class RoleOut(OrmModel):
    id: int
    code: str
    name: str
    description: str
    permissions: list[PermissionOut]


class CustomerIn(BaseModel):
    identification: str = Field(min_length=3, max_length=30)
    name: str = Field(min_length=2, max_length=160)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool = True


class CustomerOut(OrmModel):
    id: int
    identification: str
    name: str
    email: str | None
    phone: str | None
    address: str | None
    is_active: bool


class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = ""


class CategoryOut(OrmModel):
    id: int
    name: str
    description: str


class ProductIn(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    category_id: int
    sale_price: Decimal = Field(gt=0)
    cost: Decimal = Field(ge=0)
    is_active: bool = True
    initial_quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    category_id: int
    sale_price: Decimal = Field(gt=0)
    cost: Decimal = Field(ge=0)
    is_active: bool = True


class ProductOut(OrmModel):
    id: int
    sku: str
    name: str
    description: str
    category_id: int
    category_name: str
    sale_price: float
    cost: float
    is_active: bool
    quantity: int
    reorder_level: int


class MovementIn(BaseModel):
    product_id: int
    movement_type: str
    quantity: int = Field(gt=0)
    notes: str = ""


class MovementOut(OrmModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    movement_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    reference_type: str
    reference_id: int | None
    notes: str
    user_name: str | None
    created_at: datetime


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    customer_id: int
    sale_date: date
    notes: str = ""
    items: list[SaleItemIn] = Field(min_length=1)


class SaleDetailOut(BaseModel):
    id: int
    product_id: int
    sku: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class SaleOut(BaseModel):
    id: int
    number: str
    customer_id: int
    customer_name: str
    user_id: int
    user_name: str
    status: str
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    sale_date: date
    notes: str
    details: list[SaleDetailOut] = []


class DashboardOut(BaseModel):
    total_ventas: float
    cantidad_ventas: int
    productos: int
    clientes: int
    bajo_inventario: int
    ventas_por_mes: list[dict]
    productos_mas_vendidos: list[dict]
    vendedores: list[dict] | None = None
    alcance: str


class SettingsOut(BaseModel):
    company_name: str
    currency: str
    tax_rate: float
    low_stock_threshold: int


class SettingsUpdate(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    tax_rate: Decimal = Field(ge=0, le=100)
    low_stock_threshold: int = Field(ge=0, le=100000)


class AuditOut(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None
    action: str
    entity: str
    entity_id: str | None
    tool_name: str | None
    result_status: str
    message: str
    created_at: datetime


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=4, max_length=80)


class AssistantAction(BaseModel):
    type: str
    label: str
    route: str | None = None
    confirmation_token: str | None = None


class AssistantSource(BaseModel):
    title: str
    excerpt: str


class AssistantResponse(BaseModel):
    message: str
    intent: str
    sources: list[AssistantSource] = []
    actions: list[AssistantAction] = []
    data: dict | list | None = None
    available: bool = True


class ConfirmRequest(BaseModel):
    token: str = Field(min_length=8, max_length=120)

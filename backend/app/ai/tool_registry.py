import json

from pydantic import BaseModel, Field


class ConsultarVentasArgs(BaseModel):
    fecha_inicio: str | None = Field(default=None, description="Start date YYYY-MM-DD")
    fecha_fin: str | None = Field(default=None, description="End date YYYY-MM-DD")
    producto: str | None = Field(default=None, description="Product name or SKU")
    cliente: str | None = Field(default=None, description="Customer name or identification")
    usuario_responsable: str | None = Field(default=None, description="Seller username")


class ConsultarProductoArgs(BaseModel):
    nombre: str | None = Field(default=None, description="Product name")
    sku: str | None = Field(default=None, description="SKU")


class ConsultarInventarioArgs(BaseModel):
    producto: str | None = Field(default=None, description="Product name or SKU")
    categoria: str | None = Field(default=None, description="Category name")
    solo_bajo_stock: bool | None = Field(default=None, description="Only products at or below reorder level")
    cantidad_menor_que: int | None = Field(default=None, description="Only products with quantity lower than this number")


class BuscarClienteArgs(BaseModel):
    nombre: str | None = Field(default=None, description="Customer name")
    identificacion: str | None = Field(default=None, description="Identification")


class ConsultarClientesArgs(BaseModel):
    nombre: str | None = Field(default=None, description="Optional name filter")


class ConsultarProductosArgs(BaseModel):
    nombre: str | None = Field(default=None, description="Optional name or SKU")
    categoria: str | None = Field(default=None, description="Optional category")


class ConsultarUsuariosArgs(BaseModel):
    rol: str | None = Field(default=None, description="Role code ADMIN, SELLER or READER")
    nombre: str | None = Field(default=None, description="Name or username")


class ConsultarTopArgs(BaseModel):
    fecha_inicio: str | None = Field(default=None, description="Start date YYYY-MM-DD")
    fecha_fin: str | None = Field(default=None, description="End date YYYY-MM-DD")
    limite: int | None = Field(default=5, description="Maximum rows, up to 10")


class ConsultarDashboardArgs(BaseModel):
    fecha_inicio: str | None = Field(default=None, description="Start date YYYY-MM-DD")
    fecha_fin: str | None = Field(default=None, description="End date YYYY-MM-DD")


class ConsultarHistorialArgs(BaseModel):
    cliente: str = Field(description="Customer name or identification")


class ConsultaTextoArgs(BaseModel):
    consulta: str = Field(description="User question in Spanish")


class CrearClienteArgs(BaseModel):
    identificacion: str
    nombre: str
    email: str | None = None
    telefono: str | None = None


class CrearProductoArgs(BaseModel):
    sku: str
    nombre: str
    categoria: str
    precio: float
    costo: float
    cantidad: int = 0


class CrearVentaArgs(BaseModel):
    cliente: str = Field(description="Customer name or identification")
    productos: str = Field(description="Comma separated SKU:quantity pairs, for example OF-001:2, TEC-010:1")
    notas: str | None = None


class CrearUsuarioArgs(BaseModel):
    username: str
    email: str
    nombre: str
    password: str
    rol: str = Field(description="ADMIN, SELLER or READER")


class ToolSpec:
    def __init__(self, name: str, description: str, args_model: type[BaseModel], permission: str | None, sensitive: bool = False):
        self.name = name
        self.description = description
        self.args_model = args_model
        self.permission = permission
        self.sensitive = sensitive

    def schema(self) -> dict:
        raw = self.args_model.model_json_schema()
        properties = {}
        for key, value in raw.get("properties", {}).items():
            kind = value.get("type", "string")
            if "anyOf" in value:
                kinds = [item.get("type") for item in value["anyOf"] if item.get("type") and item.get("type") != "null"]
                kind = kinds[0] if kinds else "string"
            properties[key] = {"type": kind, "description": value.get("description") or key}
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": raw.get("required", []),
                },
            },
        }


def _spec(name: str, description: str, model: type[BaseModel], permission: str | None, sensitive: bool = False) -> ToolSpec:
    return ToolSpec(name, description, model, permission, sensitive)


TOOLS: dict[str, ToolSpec] = {
    item.name: item
    for item in [
        _spec("consultar_ventas", "Count confirmed sales and amount for a date range", ConsultarVentasArgs, None),
        _spec("consultar_producto", "Find one product by name or SKU, including stock", ConsultarProductoArgs, "products.read"),
        _spec("consultar_inventario", "List stock. Use cantidad_menor_que for questions about units below a number", ConsultarInventarioArgs, "inventory.read"),
        _spec("buscar_cliente", "Find customers by name or identification", BuscarClienteArgs, "customers.read"),
        _spec("consultar_clientes", "List customers", ConsultarClientesArgs, "customers.read"),
        _spec("consultar_productos", "List products", ConsultarProductosArgs, "products.read"),
        _spec("consultar_usuarios", "List users and roles. Never returns passwords", ConsultarUsuariosArgs, "users.read"),
        _spec("consultar_top_productos", "Rank products by units sold", ConsultarTopArgs, "dashboard.read"),
        _spec("consultar_top_clientes", "Rank customers by purchase amount", ConsultarTopArgs, "dashboard.read"),
        _spec("consultar_dashboard", "Company or own-sales indicators", ConsultarDashboardArgs, "dashboard.read"),
        _spec("consultar_historial_compras", "Purchase history of one customer", ConsultarHistorialArgs, "customers.read"),
        _spec("buscar_funcionalidad_erp", "Find a real ERP screen and its route", ConsultaTextoArgs, "assistant.use"),
        _spec("consultar_documentacion", "Retrieve ERP manual excerpts about how to use a feature", ConsultaTextoArgs, "assistant.use"),
        _spec("crear_cliente", "Prepare creation of a customer. Requires confirmation", CrearClienteArgs, "customers.write", True),
        _spec("crear_producto", "Prepare creation of a product. Requires confirmation", CrearProductoArgs, "products.write", True),
        _spec("crear_venta", "Prepare a confirmed sale. Requires confirmation", CrearVentaArgs, "sales.create", True),
        _spec("crear_usuario", "Prepare creation of a user. Requires confirmation", CrearUsuarioArgs, "users.write", True),
    ]
}

INTENT_TOOLS = {
    "NAVIGATION": ["buscar_funcionalidad_erp"],
    "HOW_TO": ["consultar_documentacion", "buscar_funcionalidad_erp"],
    "BUSINESS_QUERY": [
        "consultar_ventas",
        "consultar_producto",
        "consultar_inventario",
        "buscar_cliente",
        "consultar_clientes",
        "consultar_productos",
        "consultar_usuarios",
        "consultar_historial_compras",
    ],
    "ANALYTICS": ["consultar_top_productos", "consultar_top_clientes", "consultar_dashboard", "consultar_inventario", "consultar_ventas"],
    "ACTION": ["crear_cliente", "crear_producto", "crear_venta", "crear_usuario"],
    "GENERAL": ["consultar_documentacion"],
}


def parse_arguments(spec: ToolSpec, arguments) -> BaseModel:
    if isinstance(arguments, str):
        arguments = json.loads(arguments or "{}")
    return spec.args_model.model_validate(arguments or {})

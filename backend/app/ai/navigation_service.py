import unicodedata

from app.core.dependencies import has_permission
from app.models import User

FEATURES: list[dict] = [
    {
        "module": "Tablero",
        "name": "Tablero",
        "description": "Indicadores de ventas, clientes, productos y stock bajo",
        "route": "/",
        "permission": "dashboard.read",
        "keywords": ["tablero", "dashboard", "indicadores", "inicio", "panel"],
    },
    {
        "module": "Administración",
        "name": "Usuarios",
        "description": "Listado de usuarios del ERP",
        "route": "/admin/users",
        "permission": "users.read",
        "keywords": ["usuarios", "listar usuarios", "administracion", "administrar usuarios"],
    },
    {
        "module": "Administración",
        "name": "Nuevo usuario",
        "description": "Crear un usuario y asignarle un rol",
        "route": "/admin/users/new",
        "permission": "users.write",
        "keywords": ["crear usuario", "nuevo usuario", "alta de usuario", "registrar usuario", "donde creo un usuario", "donde puedo crear un usuario"],
    },
    {
        "module": "Administración",
        "name": "Roles y permisos",
        "description": "Consultar los roles administrador, vendedor y consulta",
        "route": "/admin/roles",
        "permission": "roles.read",
        "keywords": ["roles", "permisos", "administrador", "vendedor", "consulta"],
    },
    {
        "module": "Clientes",
        "name": "Clientes",
        "description": "Consultar y buscar clientes",
        "route": "/customers",
        "permission": "customers.read",
        "keywords": ["clientes", "listado de clientes", "buscar cliente"],
    },
    {
        "module": "Clientes",
        "name": "Nuevo cliente",
        "description": "Registrar un cliente",
        "route": "/customers/new",
        "permission": "customers.write",
        "keywords": ["crear cliente", "nuevo cliente", "registrar cliente", "como registro un cliente"],
    },
    {
        "module": "Productos",
        "name": "Productos",
        "description": "Catálogo de productos, precios y existencias",
        "route": "/products",
        "permission": "products.read",
        "keywords": ["productos", "catalogo", "modulo de productos", "llevame al modulo de productos", "llevame a productos"],
    },
    {
        "module": "Productos",
        "name": "Nuevo producto",
        "description": "Crear un producto con SKU, precio, costo y existencia inicial",
        "route": "/products/new",
        "permission": "products.write",
        "keywords": ["crear producto", "nuevo producto", "registrar producto"],
    },
    {
        "module": "Inventario",
        "name": "Inventario",
        "description": "Existencias actuales y alertas de stock bajo",
        "route": "/inventory",
        "permission": "inventory.read",
        "keywords": ["inventario", "existencias", "stock", "bajo inventario"],
    },
    {
        "module": "Inventario",
        "name": "Movimientos de inventario",
        "description": "Historial de entradas, salidas, ajustes y ventas",
        "route": "/inventory/movements",
        "permission": "inventory.read",
        "keywords": ["movimientos", "historial de inventario", "entradas", "salidas", "ajustes"],
    },
    {
        "module": "Ventas",
        "name": "Ventas",
        "description": "Historial de ventas confirmadas",
        "route": "/sales",
        "permission": "sales.read_own",
        "keywords": ["ventas", "historial de ventas", "mis ventas"],
    },
    {
        "module": "Ventas",
        "name": "Nueva venta",
        "description": "Registrar una venta, elegir cliente y productos y descontar inventario",
        "route": "/sales/new",
        "permission": "sales.create",
        "keywords": ["registrar una venta", "nueva venta", "como registro una venta", "crear venta", "hacer una venta"],
    },
    {
        "module": "Auditoría",
        "name": "Auditoría",
        "description": "Registro de accesos, cambios y herramientas del asistente",
        "route": "/audit",
        "permission": "audit.read",
        "keywords": ["auditoria", "registro de auditoria", "logs"],
    },
    {
        "module": "Configuración",
        "name": "Configuración",
        "description": "Nombre de la empresa, impuesto y umbral de stock bajo",
        "route": "/settings",
        "permission": "settings.write",
        "keywords": ["configuracion", "impuesto", "iva", "moneda", "umbral"],
    },
]


def normalize(text: str) -> str:
    text = text.lower().strip()
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def search_features(query: str, user: User, limit: int = 3) -> list[dict]:
    q = normalize(query)
    scored: list[tuple[int, dict]] = []
    for feature in FEATURES:
        score = 0
        for keyword in feature["keywords"]:
            key = normalize(keyword)
            if key in q or q in key:
                score += 5 + len(key)
            else:
                overlap = len(set(q.split()) & set(key.split()))
                score += overlap
        if score <= 0:
            continue
        allowed = has_permission(user, feature["permission"])
        scored.append(
            (
                score + (2 if allowed else 0),
                {
                    "modulo": feature["module"],
                    "nombre": feature["name"],
                    "descripcion": feature["description"],
                    "ruta": feature["route"] if allowed else None,
                    "permiso": feature["permission"],
                    "permitido": allowed,
                },
            )
        )
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return []
    best = scored[0][0]
    close = [item for item in scored if item[0] >= best - 3]
    return [item[1] for item in close[:limit]]

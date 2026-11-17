PERMISSIONS: list[tuple[str, str, str, str]] = [
    ("users.read", "Ver usuarios", "usuarios", "Consultar el listado de usuarios"),
    ("users.write", "Administrar usuarios", "usuarios", "Crear, editar y activar usuarios"),
    ("roles.read", "Ver roles", "roles", "Consultar roles y permisos"),
    ("customers.read", "Ver clientes", "clientes", "Consultar clientes e historial"),
    ("customers.write", "Administrar clientes", "clientes", "Crear, editar y activar clientes"),
    ("products.read", "Ver productos", "productos", "Consultar productos y categorías"),
    ("products.write", "Administrar productos", "productos", "Crear y editar productos"),
    ("inventory.read", "Ver inventario", "inventario", "Consultar existencias y movimientos"),
    ("inventory.write", "Administrar inventario", "inventario", "Registrar entradas, salidas y ajustes"),
    ("sales.create", "Registrar ventas", "ventas", "Confirmar una venta"),
    ("sales.read_own", "Ver sus ventas", "ventas", "Consultar las ventas propias"),
    ("sales.read_all", "Ver todas las ventas", "ventas", "Consultar ventas de todos los vendedores"),
    ("sales.cancel", "Anular ventas", "ventas", "Anular una venta confirmada y devolver stock"),
    ("dashboard.read", "Ver tablero", "dashboard", "Consultar indicadores"),
    ("audit.read", "Ver auditoría", "auditoria", "Consultar el registro de auditoría"),
    ("settings.write", "Configurar empresa", "configuracion", "Cambiar impuesto y umbral de stock"),
    ("assistant.use", "Usar asistente", "asistente", "Conversar con el asistente del ERP"),
    ("knowledge.index", "Reindexar documentación", "asistente", "Volver a indexar los manuales"),
]

ROLE_DEFINITIONS: list[tuple[str, str, str]] = [
    ("ADMIN", "ADMINISTRADOR", "Acceso completo al ERP"),
    ("SELLER", "VENDEDOR", "Consulta comercial y registro de sus ventas"),
    ("READER", "CONSULTA", "Lectura de clientes, productos, inventario e indicadores"),
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ADMIN": [item[0] for item in PERMISSIONS],
    "SELLER": [
        "customers.read",
        "products.read",
        "inventory.read",
        "sales.create",
        "sales.read_own",
        "sales.cancel",
        "dashboard.read",
        "assistant.use",
    ],
    "READER": [
        "customers.read",
        "products.read",
        "inventory.read",
        "dashboard.read",
        "assistant.use",
    ],
}

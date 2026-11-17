import secrets
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import has_permission
from app.core.errors import AppError
from app.models import Category, Customer, Inventory, Product, Role, Sale, SaleDetail, User
from app.schemas.dto import CustomerIn, ProductIn, SaleCreate, SaleItemIn, UserCreate
from app.ai.navigation_service import search_features
from app.ai.rag_service import retrieve
from app.ai.tool_registry import TOOLS, parse_arguments
from app.repositories.products import find_product, low_stock
from app.repositories.customers import find_customers
from app.repositories.users import list_users
from app.services.audit_service import write_audit
from app.services.customer_service import create_customer
from app.services.dashboard_service import build_dashboard
from app.services.mappers import as_float, user_out
from app.services.product_service import create_product
from app.services.sales_service import create_sale, sale_loader
from app.services.user_service import create_user

_PENDING: dict[str, dict] = {}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _dates(args) -> tuple[date, date]:
    start = _parse_date(getattr(args, "fecha_inicio", None))
    end = _parse_date(getattr(args, "fecha_fin", None))
    if start is None or end is None:
        raise AppError("Indica fecha_inicio y fecha_fin en formato YYYY-MM-DD.")
    if start > end:
        raise AppError("La fecha inicial no puede ser posterior a la fecha final.")
    return start, end


def _scope(user: User) -> str:
    if has_permission(user, "sales.read_all"):
        return "all"
    if has_permission(user, "sales.read_own"):
        return "own"
    if has_permission(user, "dashboard.read"):
        return "aggregate"
    raise AppError("No tienes permiso para consultar ventas.", 403)


def _confirmed(user: User, start: date, end: date, seller: str | None):
    filters = [Sale.status == "CONFIRMADA", Sale.sale_date >= start, Sale.sale_date <= end]
    scope = _scope(user)
    if seller:
        if scope != "all" and not (scope == "own" and seller.strip().lower() == user.username):
            raise AppError("No tienes permiso para consultar las ventas de otros vendedores.", 403)
        filters.append(
            Sale.user_id == select(User.id).where(User.username == seller.strip().lower()).scalar_subquery()
        )
    elif scope == "own":
        filters.append(Sale.user_id == user.id)
    return filters


def execute(db: Session, user: User, name: str, arguments) -> dict:
    spec = TOOLS.get(name)
    if spec is None:
        raise AppError("La herramienta solicitada no está permitida.", 403)
    if spec.permission and not has_permission(user, spec.permission):
        raise AppError("No tienes permiso para consultar esa información.", 403)
    args = parse_arguments(spec, arguments)
    if spec.sensitive:
        return _stage(db, user, name, args)
    handler = HANDLERS[name]
    data = handler(db, user, args)
    write_audit(
        db,
        user=user,
        action="TOOL",
        entity="assistant",
        tool_name=name,
        parameters=args.model_dump(),
        result_status="OK",
        message=f"Herramienta {name}",
    )
    db.commit()
    return {"ok": True, "tool": name, "data": data, "actions": data.pop("_actions", []), "sources": data.pop("_sources", [])}


def confirm(db: Session, user: User, token: str) -> dict:
    pending = _PENDING.get(token)
    if pending is None or pending["user_id"] != user.id or pending["expires"] < datetime.now(UTC):
        raise AppError("La confirmación no es válida o expiró.", 403)
    _PENDING.pop(token, None)
    spec = TOOLS[pending["tool"]]
    if spec.permission and not has_permission(user, spec.permission):
        raise AppError("No tienes permiso para confirmar esta operación.", 403)
    data = CONFIRMERS[pending["tool"]](db, user, spec.args_model.model_validate(pending["args"]))
    write_audit(
        db,
        user=user,
        action="TOOL",
        entity="assistant",
        tool_name=pending["tool"],
        parameters={key: value for key, value in pending["args"].items() if key != "password"},
        result_status="OK",
        message=f"Confirmación de {pending['tool']}",
    )
    db.commit()
    return data


def _stage(db: Session, user: User, name: str, args) -> dict:
    token = secrets.token_urlsafe(18)
    payload = args.model_dump()
    _PENDING[token] = {
        "user_id": user.id,
        "tool": name,
        "args": payload,
        "expires": datetime.now(UTC) + timedelta(minutes=10),
    }
    safe = {key: value for key, value in payload.items() if key != "password"}
    write_audit(
        db,
        user=user,
        action="TOOL",
        entity="assistant",
        tool_name=name,
        parameters=safe,
        result_status="PENDING",
        message="Operación pendiente de confirmación",
    )
    db.commit()
    return {
        "ok": True,
        "tool": name,
        "data": {"pendiente": True, "resumen": safe},
        "actions": [{"type": "CONFIRM", "label": "Confirmar operación", "confirmation_token": token}],
        "sources": [],
    }


def _ventas(db: Session, user: User, args) -> dict:
    start, end = _dates(args)
    filters = _confirmed(user, start, end, args.usuario_responsable)
    query = select(Sale).where(*filters)
    if args.cliente:
        like = f"%{args.cliente.strip()}%"
        query = query.join(Sale.customer).where(or_(Customer.name.ilike(like), Customer.identification.ilike(like)))
    sales = db.scalars(query.order_by(Sale.sale_date.desc(), Sale.id.desc())).all()
    if args.producto:
        like = f"%{args.producto.strip()}%"
        product_ids = select(Product.id).where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
        detail_rows = db.execute(
            select(func.coalesce(func.sum(SaleDetail.quantity), 0), func.coalesce(func.sum(SaleDetail.line_total), 0))
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .where(*filters, SaleDetail.product_id.in_(product_ids))
        ).one()
        units = int(detail_rows[0])
        amount = as_float(detail_rows[1])
        count = units
    else:
        count = len(sales)
        amount = as_float(sum((sale.total for sale in sales), Decimal("0")))
        units = None
    last = None
    if sales:
        sale = sales[0]
        show_seller = _scope(user) == "all"
        last = {
            "numero": sale.number,
            "fecha": sale.sale_date.isoformat(),
            "usuario": sale.user.full_name if show_seller and sale.user else None,
            "cliente": sale.customer.name if sale.customer else "",
            "total": as_float(sale.total),
        }
    return {
        "fecha_inicio": start.isoformat(),
        "fecha_fin": end.isoformat(),
        "cantidad": count,
        "importe": amount,
        "unidades": units,
        "producto": args.producto,
        "ultima_venta": last,
    }


def _producto(db: Session, user: User, args) -> dict:
    text = args.sku or args.nombre
    if not text:
        raise AppError("Indica el nombre o el SKU del producto.")
    product = find_product(db, text)
    if product is None:
        return {"encontrado": False, "consulta": text}
    return {
        "encontrado": True,
        "id": product.id,
        "sku": product.sku,
        "nombre": product.name,
        "categoria": product.category.name,
        "precio": as_float(product.sale_price),
        "costo": as_float(product.cost),
        "cantidad": product.inventory.quantity if product.inventory else 0,
        "activo": product.is_active,
    }


def _inventario(db: Session, user: User, args) -> dict:
    rows = low_stock(
        db,
        args.categoria,
        args.cantidad_menor_que,
        bool(args.solo_bajo_stock),
    )
    if args.producto:
        like = args.producto.strip().lower()
        rows = [row for row in rows if like in row.name.lower() or like in row.sku.lower()]
    items = [
        {
            "producto": row.name,
            "sku": row.sku,
            "categoria": row.category.name,
            "cantidad": row.inventory.quantity if row.inventory else 0,
            "umbral": row.inventory.reorder_level if row.inventory else 0,
        }
        for row in rows[:20]
    ]
    return {"cantidad_productos": len(rows), "items": items}


def _clientes(db: Session, user: User, args) -> dict:
    rows = find_customers(db, getattr(args, "nombre", None), getattr(args, "identificacion", None), limit=10)
    return {
        "items": [
            {"id": row.id, "nombre": row.name, "identificacion": row.identification, "activo": row.is_active}
            for row in rows
        ]
    }


def _productos(db: Session, user: User, args) -> dict:
    from app.repositories.products import list_products

    total, rows = list_products(db, args.nombre, None, False, 1, 10)
    if args.categoria:
        rows = [row for row in rows if args.categoria.lower() in row.category.name.lower()]
    return {
        "total": total,
        "items": [
            {"sku": row.sku, "nombre": row.name, "precio": as_float(row.sale_price), "cantidad": row.inventory.quantity if row.inventory else 0}
            for row in rows
        ],
    }


def _usuarios(db: Session, user: User, args) -> dict:
    role = None
    if args.rol:
        role = {"ADMINISTRADOR": "ADMIN", "VENDEDOR": "SELLER", "CONSULTA": "READER"}.get(args.rol.strip().upper(), args.rol.strip().upper())
    total, rows = list_users(db, args.nombre, role, 1, 20)
    return {
        "total": total,
        "items": [
            {"usuario": row.username, "nombre": row.full_name, "rol": row.role.name, "activo": row.is_active}
            for row in rows
        ],
    }


def _top_productos(db: Session, user: User, args) -> dict:
    start, end = _dates(args)
    limit = min(max(args.limite or 5, 1), 10)
    filters = _confirmed(user, start, end, None)
    rows = db.execute(
        select(Product.name, Product.sku, func.sum(SaleDetail.quantity), func.sum(SaleDetail.line_total))
        .join(SaleDetail, SaleDetail.product_id == Product.id)
        .join(Sale, Sale.id == SaleDetail.sale_id)
        .where(*filters)
        .group_by(Product.id, Product.name, Product.sku)
        .order_by(func.sum(SaleDetail.quantity).desc())
        .limit(limit)
    ).all()
    return {
        "fecha_inicio": start.isoformat(),
        "fecha_fin": end.isoformat(),
        "items": [
            {"producto": row[0], "sku": row[1], "unidades": int(row[2]), "importe": as_float(row[3])} for row in rows
        ],
    }


def _top_clientes(db: Session, user: User, args) -> dict:
    start, end = _dates(args)
    limit = min(max(args.limite or 5, 1), 10)
    filters = _confirmed(user, start, end, None)
    rows = db.execute(
        select(Customer.name, Customer.identification, func.count(Sale.id), func.sum(Sale.total))
        .join(Sale, Sale.customer_id == Customer.id)
        .where(*filters)
        .group_by(Customer.id, Customer.name, Customer.identification)
        .order_by(func.sum(Sale.total).desc())
        .limit(limit)
    ).all()
    return {
        "fecha_inicio": start.isoformat(),
        "fecha_fin": end.isoformat(),
        "items": [
            {"cliente": row[0], "identificacion": row[1], "compras": int(row[2]), "importe": as_float(row[3])}
            for row in rows
        ],
    }


def _dashboard(db: Session, user: User, args) -> dict:
    start = _parse_date(args.fecha_inicio)
    end = _parse_date(args.fecha_fin)
    data = build_dashboard(db, user, start, end)
    payload = data.model_dump()
    if not has_permission(user, "sales.read_all"):
        payload["vendedores"] = None
    return payload


def _historial(db: Session, user: User, args) -> dict:
    rows = find_customers(db, args.cliente, args.cliente, limit=1)
    if not rows:
        rows = find_customers(db, args.cliente, None, limit=1)
    if not rows:
        return {"encontrado": False, "cliente": args.cliente, "items": []}
    customer = rows[0]
    sales = db.scalars(
        sale_loader().where(Sale.customer_id == customer.id, Sale.status == "CONFIRMADA").order_by(Sale.sale_date.desc()).limit(10)
    ).all()
    show_seller = has_permission(user, "sales.read_all")
    return {
        "encontrado": True,
        "cliente": customer.name,
        "items": [
            {
                "numero": sale.number,
                "fecha": sale.sale_date.isoformat(),
                "total": as_float(sale.total),
                "vendedor": sale.user.full_name if show_seller else None,
            }
            for sale in sales
        ],
    }


def _navegacion(db: Session, user: User, args) -> dict:
    matches = search_features(args.consulta, user)
    actions = []
    for match in matches:
        if match["permitido"] and match["ruta"]:
            actions.append({"type": "NAVIGATE", "label": match["nombre"], "route": match["ruta"]})
    return {"resultados": matches, "_actions": actions}


def _documentacion(db: Session, user: User, args) -> dict:
    chunks = retrieve(args.consulta)
    sources = [{"title": chunk["title"], "excerpt": chunk["excerpt"]} for chunk in chunks]
    return {"fragmentos": sources, "_sources": sources}


def _crear_cliente(db: Session, user: User, args) -> dict:
    customer = create_customer(
        db,
        user,
        CustomerIn(identification=args.identificacion, name=args.nombre, email=args.email, phone=args.telefono),
    )
    return {"id": customer.id, "nombre": customer.name}


def _crear_producto(db: Session, user: User, args) -> dict:
    category = db.scalar(select(Category).where(Category.name.ilike(args.categoria.strip())))
    if category is None:
        raise AppError("La categoría no existe.", 404)
    product = create_product(
        db,
        user,
        ProductIn(
            sku=args.sku,
            name=args.nombre,
            category_id=category.id,
            sale_price=Decimal(str(args.precio)),
            cost=Decimal(str(args.costo)),
            initial_quantity=args.cantidad,
        ),
    )
    return {"id": product.id, "sku": product.sku, "nombre": product.name}


def _crear_venta(db: Session, user: User, args) -> dict:
    customers = find_customers(db, args.cliente, args.cliente, limit=1) or find_customers(db, args.cliente, None, limit=1)
    if not customers:
        raise AppError("No encontré ese cliente.", 404)
    items = []
    for piece in args.productos.split(","):
        piece = piece.strip()
        if not piece or ":" not in piece:
            raise AppError("Cada producto debe indicarse como SKU:cantidad.")
        sku, raw_qty = piece.split(":", 1)
        product = find_product(db, sku.strip())
        if product is None:
            raise AppError(f"No encontré el producto {sku.strip()}.", 404)
        items.append(SaleItemIn(product_id=product.id, quantity=int(raw_qty.strip())))
    sale = create_sale(
        db,
        user,
        SaleCreate(customer_id=customers[0].id, sale_date=date.today(), notes=args.notas or "", items=items),
    )
    return {"numero": sale.number, "total": as_float(sale.total)}


def _crear_usuario(db: Session, user: User, args) -> dict:
    role_code = {"ADMINISTRADOR": "ADMIN", "VENDEDOR": "SELLER", "CONSULTA": "READER"}.get(args.rol.strip().upper(), args.rol.strip().upper())
    role = db.scalar(select(Role).where(Role.code == role_code))
    if role is None:
        raise AppError("El rol no existe.", 404)
    created = create_user(
        db,
        user,
        UserCreate(username=args.username, email=args.email, full_name=args.nombre, password=args.password, role_id=role.id),
    )
    safe = user_out(created)
    return {"id": safe.id, "usuario": safe.username, "rol": safe.role_name}


HANDLERS = {
    "consultar_ventas": _ventas,
    "consultar_producto": _producto,
    "consultar_inventario": _inventario,
    "buscar_cliente": _clientes,
    "consultar_clientes": _clientes,
    "consultar_productos": _productos,
    "consultar_usuarios": _usuarios,
    "consultar_top_productos": _top_productos,
    "consultar_top_clientes": _top_clientes,
    "consultar_dashboard": _dashboard,
    "consultar_historial_compras": _historial,
    "buscar_funcionalidad_erp": _navegacion,
    "consultar_documentacion": _documentacion,
}

CONFIRMERS = {
    "crear_cliente": _crear_cliente,
    "crear_producto": _crear_producto,
    "crear_venta": _crear_venta,
    "crear_usuario": _crear_usuario,
}

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import has_permission
from app.core.errors import AppError
from app.models import Customer, Inventory, Product, Sale, SaleDetail, User
from app.schemas.dto import DashboardOut
from app.services.mappers import as_float


def sales_user_filter(user: User) -> int | None:
    if not has_permission(user, "dashboard.read") and not has_permission(user, "sales.read_all"):
        raise AppError("No tienes permiso para consultar el tablero.", 403)
    if has_permission(user, "sales.read_own") and not has_permission(user, "sales.read_all"):
        return user.id
    return None


def build_dashboard(db: Session, user: User, date_from: date | None = None, date_to: date | None = None) -> DashboardOut:
    seller_id = sales_user_filter(user)
    sale_filters = [Sale.status == "CONFIRMADA"]
    if seller_id is not None:
        sale_filters.append(Sale.user_id == seller_id)
    if date_from:
        sale_filters.append(Sale.sale_date >= date_from)
    if date_to:
        sale_filters.append(Sale.sale_date <= date_to)

    totals = db.execute(
        select(func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0)).where(*sale_filters)
    ).one()
    products = db.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))) or 0
    customers = db.scalar(select(func.count(Customer.id)).where(Customer.is_active.is_(True))) or 0
    low_stock = db.scalar(
        select(func.count(Inventory.id)).where(Inventory.quantity <= Inventory.reorder_level)
    ) or 0

    month = func.to_char(Sale.sale_date, "YYYY-MM")
    month_rows = db.execute(
        select(month, func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0))
        .where(*sale_filters)
        .group_by(month)
        .order_by(month)
    ).all()
    ventas_por_mes = [
        {"mes": row[0], "cantidad": int(row[1]), "importe": as_float(row[2])} for row in month_rows
    ]

    top_rows = db.execute(
        select(Product.name, Product.sku, func.sum(SaleDetail.quantity), func.sum(SaleDetail.line_total))
        .join(SaleDetail, SaleDetail.product_id == Product.id)
        .join(Sale, Sale.id == SaleDetail.sale_id)
        .where(*sale_filters)
        .group_by(Product.id, Product.name, Product.sku)
        .order_by(func.sum(SaleDetail.quantity).desc())
        .limit(5)
    ).all()
    top_products = [
        {"producto": row[0], "sku": row[1], "unidades": int(row[2]), "importe": as_float(row[3])} for row in top_rows
    ]

    sellers = None
    if has_permission(user, "sales.read_all"):
        seller_rows = db.execute(
            select(User.full_name, User.username, func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0))
            .join(User, User.id == Sale.user_id)
            .where(*sale_filters)
            .group_by(User.id, User.full_name, User.username)
            .order_by(func.sum(Sale.total).desc())
        ).all()
        sellers = [
            {"vendedor": row[0], "usuario": row[1], "cantidad": int(row[2]), "importe": as_float(row[3])}
            for row in seller_rows
        ]

    return DashboardOut(
        total_ventas=as_float(totals[1]),
        cantidad_ventas=int(totals[0]),
        productos=int(products),
        clientes=int(customers),
        bajo_inventario=int(low_stock),
        ventas_por_mes=ventas_por_mes,
        productos_mas_vendidos=top_products,
        vendedores=sellers,
        alcance="propias" if seller_id is not None else "empresa",
    )

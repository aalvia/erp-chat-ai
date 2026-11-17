from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import has_permission
from app.core.errors import AppError
from app.models import Customer, Inventory, InventoryMovement, Product, Sale, SaleDetail, User
from app.schemas.dto import SaleCreate
from app.services.audit_service import write_audit
from app.services.settings_service import get_company_settings


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def sale_loader():
    return select(Sale).options(
        selectinload(Sale.customer),
        selectinload(Sale.user),
        selectinload(Sale.details).selectinload(SaleDetail.product),
    )


def scoped_sales(db: Session, user: User, seller_username: str | None = None):
    query = sale_loader().order_by(Sale.sale_date.desc(), Sale.id.desc())
    if has_permission(user, "sales.read_all"):
        if seller_username:
            seller = db.scalar(select(User).where(User.username == seller_username.strip().lower()))
            if seller is None:
                raise AppError("El vendedor indicado no existe.", 404)
            query = query.where(Sale.user_id == seller.id)
        return query
    if has_permission(user, "sales.read_own"):
        if seller_username and seller_username.strip().lower() != user.username:
            raise AppError("No tienes permiso para consultar las ventas de otros vendedores.", 403)
        return query.where(Sale.user_id == user.id)
    raise AppError("No tienes permiso para consultar ventas.", 403)


def list_purchases(db: Session, customer_id: int, page: int, page_size: int):
    query = sale_loader().where(Sale.customer_id == customer_id).order_by(Sale.sale_date.desc(), Sale.id.desc())
    rows = db.scalars(query).all()
    total = len(rows)
    start = (page - 1) * page_size
    return total, rows[start : start + page_size]


def list_sales(
    db: Session,
    user: User,
    page: int,
    page_size: int,
    customer_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = scoped_sales(db, user)
    if customer_id:
        query = query.where(Sale.customer_id == customer_id)
    if status:
        query = query.where(Sale.status == status.strip().upper())
    if date_from:
        query = query.where(Sale.sale_date >= date_from)
    if date_to:
        query = query.where(Sale.sale_date <= date_to)
    rows = db.scalars(query).all()
    total = len(rows)
    start = (page - 1) * page_size
    return total, rows[start : start + page_size]


def get_sale(db: Session, user: User, sale_id: int) -> Sale:
    sale = db.scalar(scoped_sales(db, user).where(Sale.id == sale_id))
    if sale is None:
        raise AppError("La venta no existe o no puedes consultarla.", 404)
    return sale


def create_sale(db: Session, user: User, data: SaleCreate) -> Sale:
    if not has_permission(user, "sales.create"):
        raise AppError("No tienes permiso para registrar ventas.", 403)
    customer = db.get(Customer, data.customer_id)
    if customer is None or not customer.is_active:
        raise AppError("El cliente no existe o está inactivo.", 404)
    if not data.items:
        raise AppError("La venta debe incluir al menos un producto.")
    seen: set[int] = set()
    prepared: list[tuple[Product, int]] = []
    for item in data.items:
        if item.product_id in seen:
            raise AppError("No repitas el mismo producto en la venta. Suma la cantidad en una línea.")
        seen.add(item.product_id)
        product = db.get(Product, item.product_id)
        if product is None or not product.is_active:
            raise AppError("Hay un producto inexistente o inactivo.", 404)
        prepared.append((product, item.quantity))
    settings = get_company_settings(db)
    try:
        locked: list[tuple[Product, Inventory, int, Decimal]] = []
        subtotal = Decimal("0")
        for product, quantity in prepared:
            inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id).with_for_update())
            available = 0 if inventory is None else inventory.quantity
            if inventory is None or available < quantity:
                raise AppError(f"Existencias insuficientes para {product.name}. Disponible: {available}.", 409)
            line_total = money(product.sale_price * quantity)
            subtotal += line_total
            locked.append((product, inventory, quantity, line_total))
        tax_rate = Decimal(settings.tax_rate)
        tax_amount = money(subtotal * tax_rate / Decimal("100"))
        total = money(subtotal + tax_amount)
        sale = Sale(
            number="TMP",
            customer_id=customer.id,
            user_id=user.id,
            status="CONFIRMADA",
            subtotal=money(subtotal),
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=total,
            sale_date=data.sale_date,
            notes=(data.notes or "").strip(),
        )
        db.add(sale)
        db.flush()
        sale.number = f"V-{sale.sale_date.year}-{sale.id:06d}"
        now = datetime.now(UTC)
        for product, inventory, quantity, line_total in locked:
            previous = inventory.quantity
            inventory.quantity = previous - quantity
            inventory.updated_at = now
            db.add(
                SaleDetail(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.sale_price,
                    line_total=line_total,
                )
            )
            db.add(
                InventoryMovement(
                    product_id=product.id,
                    movement_type="VENTA",
                    quantity=quantity,
                    previous_quantity=previous,
                    new_quantity=inventory.quantity,
                    reference_type="VENTA",
                    reference_id=sale.id,
                    notes=f"Venta {sale.number}",
                    user_id=user.id,
                )
            )
        write_audit(
            db,
            user=user,
            action="SALE",
            entity="sale",
            entity_id=sale.id,
            parameters={"total": str(total), "items": len(locked)},
            message=f"Venta {sale.number} confirmada",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return db.scalar(sale_loader().where(Sale.id == sale.id))


def cancel_sale(db: Session, user: User, sale_id: int) -> Sale:
    if not has_permission(user, "sales.cancel"):
        raise AppError("No tienes permiso para anular ventas.", 403)
    sale = db.scalar(sale_loader().where(Sale.id == sale_id).with_for_update())
    if sale is None:
        raise AppError("La venta no existe.", 404)
    if not has_permission(user, "sales.read_all") and sale.user_id != user.id:
        raise AppError("Solo puedes anular tus propias ventas.", 403)
    if sale.status != "CONFIRMADA":
        raise AppError("Solo se puede anular una venta confirmada.")
    try:
        now = datetime.now(UTC)
        for detail in sale.details:
            inventory = db.scalar(select(Inventory).where(Inventory.product_id == detail.product_id).with_for_update())
            if inventory is None:
                raise AppError("No se encontró el inventario del producto.", 409)
            previous = inventory.quantity
            inventory.quantity = previous + detail.quantity
            inventory.updated_at = now
            db.add(
                InventoryMovement(
                    product_id=detail.product_id,
                    movement_type="ENTRADA",
                    quantity=detail.quantity,
                    previous_quantity=previous,
                    new_quantity=inventory.quantity,
                    reference_type="ANULACION",
                    reference_id=sale.id,
                    notes=f"Anulación {sale.number}",
                    user_id=user.id,
                )
            )
        sale.status = "ANULADA"
        write_audit(db, user=user, action="CANCEL", entity="sale", entity_id=sale.id, message=f"Venta {sale.number} anulada")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return db.scalar(sale_loader().where(Sale.id == sale.id))

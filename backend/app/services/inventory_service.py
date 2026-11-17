from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models import Inventory, InventoryMovement, Product, User
from app.schemas.dto import MovementIn
from app.services.audit_service import write_audit

ALLOWED = {"ENTRADA", "SALIDA", "AJUSTE"}


def list_stock(db: Session):
    return db.scalars(
        select(Inventory).options(selectinload(Inventory.product).selectinload(Product.category)).order_by(Inventory.id)
    ).all()


def list_movements(db: Session, product_id: int | None, page: int, page_size: int):
    query = (
        select(InventoryMovement)
        .options(selectinload(InventoryMovement.product), selectinload(InventoryMovement.user))
        .order_by(InventoryMovement.id.desc())
    )
    if product_id:
        query = query.where(InventoryMovement.product_id == product_id)
    rows = db.scalars(query).all()
    total = len(rows)
    start = (page - 1) * page_size
    return total, rows[start : start + page_size]


def register_movement(db: Session, actor: User, data: MovementIn) -> InventoryMovement:
    movement_type = data.movement_type.strip().upper()
    if movement_type not in ALLOWED:
        raise AppError("El tipo de movimiento debe ser ENTRADA, SALIDA o AJUSTE.")
    product = db.get(Product, data.product_id)
    if product is None:
        raise AppError("El producto no existe.", 404)
    inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id).with_for_update())
    if inventory is None:
        raise AppError("El producto no tiene inventario.", 404)
    previous = inventory.quantity
    if movement_type == "ENTRADA":
        new_quantity = previous + data.quantity
        moved = data.quantity
    elif movement_type == "SALIDA":
        if previous < data.quantity:
            raise AppError(f"Existencias insuficientes para {product.name}. Disponible: {previous}.", 409)
        new_quantity = previous - data.quantity
        moved = data.quantity
    else:
        new_quantity = data.quantity
        moved = abs(new_quantity - previous)
    inventory.quantity = new_quantity
    inventory.updated_at = datetime.now(UTC)
    movement = InventoryMovement(
        product_id=product.id,
        movement_type=movement_type,
        quantity=moved,
        previous_quantity=previous,
        new_quantity=new_quantity,
        reference_type="MANUAL",
        notes=data.notes.strip(),
        user_id=actor.id,
    )
    db.add(movement)
    write_audit(
        db,
        user=actor,
        action="INVENTORY",
        entity="product",
        entity_id=product.id,
        parameters={"type": movement_type, "quantity": data.quantity, "new_quantity": new_quantity},
        message=f"{movement_type} de {product.sku}",
    )
    db.commit()
    db.refresh(movement)
    return db.scalar(
        select(InventoryMovement)
        .options(selectinload(InventoryMovement.product), selectinload(InventoryMovement.user))
        .where(InventoryMovement.id == movement.id)
    )

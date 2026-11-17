from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Category, Inventory, InventoryMovement, Product, User
from app.repositories.products import list_categories, list_products
from app.schemas.dto import CategoryIn, ProductIn, ProductUpdate
from app.services.audit_service import write_audit
from app.services.settings_service import get_company_settings


def search_products(db: Session, search: str | None, category_id: int | None, include_inactive: bool, page: int, page_size: int):
    return list_products(db, search, category_id, include_inactive, page, page_size)


def categories(db: Session) -> list[Category]:
    return list_categories(db)


def create_category(db: Session, actor: User, data: CategoryIn) -> Category:
    name = data.name.strip()
    if db.scalar(select(Category.id).where(func.lower(Category.name) == name.lower())):
        raise AppError("Ya existe una categoría con ese nombre.", 409)
    category = Category(name=name, description=data.description.strip())
    db.add(category)
    db.flush()
    write_audit(db, user=actor, action="CREATE", entity="category", entity_id=category.id, message=f"Categoría {name}")
    db.commit()
    db.refresh(category)
    return category


def get_product(db: Session, product_id: int) -> Product:
    product = db.scalar(
        select(Product).where(Product.id == product_id)
    )
    if product is None:
        raise AppError("El producto no existe.", 404)
    db.refresh(product)
    return product


def _load(db: Session, product_id: int) -> Product:
    from app.repositories.products import product_query

    product = db.scalar(product_query().where(Product.id == product_id))
    if product is None:
        raise AppError("El producto no existe.", 404)
    return product


def create_product(db: Session, actor: User, data: ProductIn) -> Product:
    sku = data.sku.strip().upper()
    if db.scalar(select(Product.id).where(func.lower(Product.sku) == sku.lower())):
        raise AppError("Ya existe un producto con ese SKU.", 409)
    category = db.get(Category, data.category_id)
    if category is None:
        raise AppError("La categoría no existe.", 404)
    if data.cost > data.sale_price:
        raise AppError("El costo no puede ser mayor que el precio de venta.")
    settings = get_company_settings(db)
    product = Product(
        sku=sku,
        name=data.name.strip(),
        description=data.description.strip(),
        category_id=category.id,
        sale_price=Decimal(data.sale_price),
        cost=Decimal(data.cost),
        is_active=data.is_active,
        updated_at=datetime.now(UTC),
    )
    db.add(product)
    db.flush()
    inventory = Inventory(
        product_id=product.id,
        quantity=data.initial_quantity,
        reorder_level=settings.low_stock_threshold,
        updated_at=datetime.now(UTC),
    )
    db.add(inventory)
    if data.initial_quantity:
        db.add(
            InventoryMovement(
                product_id=product.id,
                movement_type="ENTRADA",
                quantity=data.initial_quantity,
                previous_quantity=0,
                new_quantity=data.initial_quantity,
                reference_type="ALTA",
                notes="Existencia inicial",
                user_id=actor.id,
            )
        )
    write_audit(
        db,
        user=actor,
        action="CREATE",
        entity="product",
        entity_id=product.id,
        parameters={"sku": sku, "initial_quantity": data.initial_quantity},
        message=f"Producto {sku} creado",
    )
    db.commit()
    return _load(db, product.id)


def update_product(db: Session, actor: User, product_id: int, data: ProductUpdate) -> Product:
    product = _load(db, product_id)
    sku = data.sku.strip().upper()
    existing = db.scalar(select(Product.id).where(func.lower(Product.sku) == sku.lower(), Product.id != product.id))
    if existing:
        raise AppError("Ya existe un producto con ese SKU.", 409)
    category = db.get(Category, data.category_id)
    if category is None:
        raise AppError("La categoría no existe.", 404)
    if data.cost > data.sale_price:
        raise AppError("El costo no puede ser mayor que el precio de venta.")
    product.sku = sku
    product.name = data.name.strip()
    product.description = data.description.strip()
    product.category_id = category.id
    product.sale_price = Decimal(data.sale_price)
    product.cost = Decimal(data.cost)
    product.is_active = data.is_active
    product.updated_at = datetime.now(UTC)
    write_audit(db, user=actor, action="UPDATE", entity="product", entity_id=product.id, message=f"Producto {sku} actualizado")
    db.commit()
    return _load(db, product.id)

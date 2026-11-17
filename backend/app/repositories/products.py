from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Category, Inventory, Product


def product_query():
    return select(Product).options(selectinload(Product.category), selectinload(Product.inventory)).order_by(Product.name)


def list_products(
    db: Session,
    search: str | None,
    category_id: int | None,
    include_inactive: bool,
    page: int,
    page_size: int,
):
    query = product_query()
    if search:
        like = f"%{search.strip()}%"
        query = query.where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    if category_id:
        query = query.where(Product.category_id == category_id)
    if not include_inactive:
        query = query.where(Product.is_active.is_(True))
    rows = db.scalars(query).all()
    total = len(rows)
    start = (page - 1) * page_size
    return total, rows[start : start + page_size]


def find_product(db: Session, text: str) -> Product | None:
    like = text.strip()
    query = product_query().where(or_(Product.sku.ilike(like), Product.name.ilike(f"%{like}%")))
    return db.scalars(query.limit(1)).first()


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)).all())


def low_stock(db: Session, category: str | None, below: int | None, only_low: bool):
    query = product_query().join(Product.inventory)
    if category:
        query = query.join(Product.category).where(Category.name.ilike(f"%{category.strip()}%"))
    rows = db.scalars(query).all()
    result = []
    for product in rows:
        quantity = product.inventory.quantity if product.inventory else 0
        level = product.inventory.reorder_level if product.inventory else 0
        if below is not None and quantity >= below:
            continue
        if only_low and quantity > level:
            continue
        result.append(product)
    return result

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import CategoryIn, CategoryOut, Page, ProductIn, ProductOut, ProductUpdate
from app.services.mappers import product_out
from app.services.product_service import categories, create_category, create_product, search_products, update_product

router = APIRouter(prefix="/products", tags=["Productos"])


@router.get("/categories", response_model=list[CategoryOut])
def get_categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("products.read")),
):
    return categories(db)


@router.post("/categories", response_model=CategoryOut, status_code=201)
def post_category(
    data: CategoryIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.write")),
):
    return create_category(db, actor, data)


@router.get("", response_model=Page)
def get_products(
    search: str | None = None,
    category_id: int | None = None,
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("products.read")),
):
    total, rows = search_products(db, search, category_id, include_inactive, page, page_size)
    return Page(items=[product_out(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=ProductOut, status_code=201)
def post_product(
    data: ProductIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.write")),
):
    return product_out(create_product(db, actor, data))


@router.put("/{product_id}", response_model=ProductOut)
def put_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("products.write")),
):
    return product_out(update_product(db, actor, product_id, data))

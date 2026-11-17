from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import MovementIn, MovementOut, Page
from app.services.inventory_service import list_movements, list_stock, register_movement
from app.services.mappers import movement_out, product_out

router = APIRouter(prefix="/inventory", tags=["Inventario"])


@router.get("", response_model=Page)
def get_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("inventory.read")),
):
    rows = list_stock(db)
    total = len(rows)
    start = (page - 1) * page_size
    items = []
    for row in rows[start : start + page_size]:
        item = product_out(row.product)
        items.append(item)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/movements", response_model=Page)
def get_movements(
    product_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("inventory.read")),
):
    total, rows = list_movements(db, product_id, page, page_size)
    return Page(items=[movement_out(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("/movements", response_model=MovementOut, status_code=201)
def post_movement(
    data: MovementIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("inventory.write")),
):
    return movement_out(register_movement(db, actor, data))

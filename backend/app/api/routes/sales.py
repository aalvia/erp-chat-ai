from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import Page, SaleCreate, SaleOut
from app.services.mappers import sale_out
from app.services.sales_service import cancel_sale, create_sale, get_sale, list_sales

router = APIRouter(prefix="/sales", tags=["Ventas"])


@router.get("", response_model=Page)
def get_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    total, rows = list_sales(db, actor, page, page_size, customer_id, status, date_from, date_to)
    return Page(items=[sale_out(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=SaleOut, status_code=201)
def post_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("sales.create")),
):
    return sale_out(create_sale(db, actor, data), with_details=True)


@router.get("/{sale_id}", response_model=SaleOut)
def get_one(
    sale_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    return sale_out(get_sale(db, actor, sale_id), with_details=True)


@router.post("/{sale_id}/cancel", response_model=SaleOut)
def post_cancel(
    sale_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("sales.cancel")),
):
    return sale_out(cancel_sale(db, actor, sale_id), with_details=True)

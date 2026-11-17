from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import CustomerIn, CustomerOut, Page, SaleOut
from app.services.customer_service import create_customer, get_customer, search_customers, update_customer
from app.services.mappers import customer_out, sale_out
from app.core.dependencies import has_permission
from app.services.sales_service import list_purchases

router = APIRouter(prefix="/customers", tags=["Clientes"])


@router.get("", response_model=Page)
def get_customers(
    search: str | None = None,
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customers.read")),
):
    total, rows = search_customers(db, search, include_inactive, page, page_size)
    return Page(items=[customer_out(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=CustomerOut, status_code=201)
def post_customer(
    data: CustomerIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("customers.write")),
):
    return customer_out(create_customer(db, actor, data))


@router.get("/{customer_id}", response_model=CustomerOut)
def get_one(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("customers.read")),
):
    return customer_out(get_customer(db, customer_id))


@router.put("/{customer_id}", response_model=CustomerOut)
def put_customer(
    customer_id: int,
    data: CustomerIn,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("customers.write")),
):
    return customer_out(update_customer(db, actor, customer_id, data))


@router.get("/{customer_id}/purchases", response_model=Page)
def purchases(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("customers.read")),
):
    get_customer(db, customer_id)
    total, rows = list_purchases(db, customer_id, page, page_size)
    items = []
    for row in rows:
        item = sale_out(row)
        if not has_permission(actor, "sales.read_all"):
            item.user_name = "Reservado"
            item.user_id = 0
        items.append(item)
    return Page(items=items, total=total, page=page, page_size=page_size)

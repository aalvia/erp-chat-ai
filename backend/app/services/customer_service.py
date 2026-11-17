from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Customer, User
from app.repositories.customers import find_customers, list_customers
from app.schemas.dto import CustomerIn
from app.services.audit_service import write_audit


def search_customers(db: Session, search: str | None, include_inactive: bool, page: int, page_size: int):
    return list_customers(db, search, include_inactive, page, page_size)


def get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise AppError("El cliente no existe.", 404)
    return customer


def create_customer(db: Session, actor: User, data: CustomerIn) -> Customer:
    identification = data.identification.strip()
    if db.scalar(select(Customer.id).where(func.lower(Customer.identification) == identification.lower())):
        raise AppError("Ya existe un cliente con esa identificación.", 409)
    customer = Customer(
        identification=identification,
        name=data.name.strip(),
        email=(data.email or "").strip() or None,
        phone=(data.phone or "").strip() or None,
        address=(data.address or "").strip() or None,
        is_active=data.is_active,
        updated_at=datetime.now(UTC),
    )
    db.add(customer)
    db.flush()
    write_audit(
        db,
        user=actor,
        action="CREATE",
        entity="customer",
        entity_id=customer.id,
        parameters={"identification": identification},
        message=f"Cliente {customer.name} creado",
    )
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, actor: User, customer_id: int, data: CustomerIn) -> Customer:
    customer = get_customer(db, customer_id)
    identification = data.identification.strip()
    existing = db.scalar(
        select(Customer.id).where(
            func.lower(Customer.identification) == identification.lower(),
            Customer.id != customer.id,
        )
    )
    if existing:
        raise AppError("Ya existe un cliente con esa identificación.", 409)
    customer.identification = identification
    customer.name = data.name.strip()
    customer.email = (data.email or "").strip() or None
    customer.phone = (data.phone or "").strip() or None
    customer.address = (data.address or "").strip() or None
    customer.is_active = data.is_active
    customer.updated_at = datetime.now(UTC)
    write_audit(
        db,
        user=actor,
        action="UPDATE",
        entity="customer",
        entity_id=customer.id,
        message=f"Cliente {customer.name} actualizado",
    )
    db.commit()
    db.refresh(customer)
    return customer

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Customer


def list_customers(db: Session, search: str | None, include_inactive: bool, page: int, page_size: int):
    query = select(Customer).order_by(Customer.name)
    if search:
        like = f"%{search.strip()}%"
        query = query.where(or_(Customer.name.ilike(like), Customer.identification.ilike(like)))
    if not include_inactive:
        query = query.where(Customer.is_active.is_(True))
    rows = db.scalars(query).all()
    total = len(rows)
    start = (page - 1) * page_size
    return total, rows[start : start + page_size]


def find_customers(db: Session, name: str | None, identification: str | None, limit: int = 10):
    query = select(Customer).where(Customer.is_active.is_(True)).order_by(Customer.name)
    if identification:
        query = query.where(Customer.identification.ilike(f"%{identification.strip()}%"))
    if name:
        query = query.where(Customer.name.ilike(f"%{name.strip()}%"))
    return db.scalars(query.limit(limit)).all()

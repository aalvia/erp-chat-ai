from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Role, User


def user_query():
    return select(User).options(selectinload(User.role).selectinload(Role.permissions))


def get_user(db: Session, user_id: int) -> User | None:
    return db.scalar(user_query().where(User.id == user_id))


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(user_query().where(User.username == username))


def list_users(db: Session, search: str | None, role_code: str | None, page: int, page_size: int):
    query = user_query().order_by(User.id)
    count = select(User.id)
    if search:
        like = f"%{search.strip()}%"
        condition = or_(User.username.ilike(like), User.full_name.ilike(like), User.email.ilike(like))
        query = query.where(condition)
        count = count.where(condition)
    if role_code:
        query = query.join(User.role).where(Role.code == role_code)
        count = count.join(User.role).where(Role.code == role_code)
    total = len(db.scalars(count).all())
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return total, rows

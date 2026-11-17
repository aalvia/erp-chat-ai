from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import Page, StatusUpdate, UserCreate, UserOut, UserUpdate
from app.services.mappers import user_out
from app.services.user_service import create_user, search_users, set_status, update_user

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("", response_model=Page)
def get_users(
    search: str | None = None,
    role: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.read")),
):
    total, rows = search_users(db, search, role, page, page_size)
    return Page(items=[user_out(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=UserOut, status_code=201)
def post_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.write")),
):
    return user_out(create_user(db, actor, data))


@router.put("/{user_id}", response_model=UserOut)
def put_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.write")),
):
    return user_out(update_user(db, actor, user_id, data))


@router.patch("/{user_id}/status", response_model=UserOut)
def patch_status(
    user_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("users.write")),
):
    return user_out(set_status(db, actor, user_id, data.is_active))

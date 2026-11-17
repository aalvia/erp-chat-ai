from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import Role, User
from app.schemas.dto import RoleOut
from app.services.mappers import role_out

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleOut])
def get_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("roles.read")),
):
    roles = db.scalars(select(Role).options(selectinload(Role.permissions)).order_by(Role.id)).all()
    return [role_out(role) for role in roles]

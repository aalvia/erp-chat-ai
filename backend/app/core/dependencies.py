from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import Role, User

bearer = HTTPBearer(auto_error=False)


def has_permission(user: User, code: str) -> bool:
    return any(permission.code == code for permission in user.role.permissions)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
        token_version = int(payload["tv"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="La sesión no es válida.")
    user = db.scalar(
        select(User)
        .options(selectinload(User.role).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    if user is None or not user.is_active or user.token_version != token_version:
        raise HTTPException(status_code=401, detail="La sesión no es válida o el usuario está inactivo.")
    return user


def require_permissions(*codes: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        missing = [code for code in codes if not has_permission(user, code)]
        if missing:
            raise AppError("No tienes permiso para esta operación.", 403)
        return user

    return checker

import re
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models import Role, User
from app.repositories.users import get_by_username, get_user, list_users
from app.schemas.dto import UserCreate, UserUpdate
from app.services.audit_service import write_audit

PASSWORD_RULE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def validate_password(password: str) -> None:
    if PASSWORD_RULE.match(password) is None:
        raise AppError("La contraseña debe tener al menos 8 caracteres, una letra y un número.")


def authenticate(db: Session, username: str, password: str) -> User:
    user = get_by_username(db, username.strip())
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        write_audit(
            db,
            user=user,
            action="LOGIN",
            entity="user",
            entity_id=None if user is None else user.id,
            result_status="DENIED",
            message="Intento de acceso rechazado",
        )
        db.commit()
        raise AppError("Usuario o contraseña incorrectos.", 401)
    write_audit(db, user=user, action="LOGIN", entity="user", entity_id=user.id, message="Inicio de sesión")
    db.commit()
    return user


def search_users(db: Session, search: str | None, role_code: str | None, page: int, page_size: int):
    return list_users(db, search, role_code, page, page_size)


def create_user(db: Session, actor: User, data: UserCreate) -> User:
    validate_password(data.password)
    username = data.username.strip().lower()
    email = data.email.strip().lower()
    if db.scalar(select(User.id).where(func.lower(User.username) == username)):
        raise AppError("Ya existe un usuario con ese nombre.", 409)
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise AppError("Ya existe un usuario con ese correo.", 409)
    role = db.get(Role, data.role_id)
    if role is None:
        raise AppError("El rol no existe.", 404)
    user = User(
        username=username,
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role_id=role.id,
        is_active=data.is_active,
        token_version=1,
        updated_at=datetime.now(UTC),
    )
    db.add(user)
    db.flush()
    write_audit(
        db,
        user=actor,
        action="CREATE",
        entity="user",
        entity_id=user.id,
        parameters={"username": username, "role": role.code},
        message=f"Usuario {username} creado",
    )
    db.commit()
    return get_user(db, user.id)


def update_user(db: Session, actor: User, user_id: int, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    if user is None:
        raise AppError("El usuario no existe.", 404)
    if user.id == actor.id and not data.is_active:
        raise AppError("No puedes desactivar tu propio usuario.")
    email = data.email.strip().lower()
    existing = db.scalar(select(User.id).where(func.lower(User.email) == email, User.id != user.id))
    if existing:
        raise AppError("Ya existe un usuario con ese correo.", 409)
    role = db.get(Role, data.role_id)
    if role is None:
        raise AppError("El rol no existe.", 404)
    user.email = email
    user.full_name = data.full_name.strip()
    user.role_id = role.id
    user.is_active = data.is_active
    user.updated_at = datetime.now(UTC)
    if data.password:
        validate_password(data.password)
        user.password_hash = hash_password(data.password)
        user.token_version += 1
    if not data.is_active:
        user.token_version += 1
    write_audit(
        db,
        user=actor,
        action="UPDATE",
        entity="user",
        entity_id=user.id,
        parameters={"role": role.code, "is_active": data.is_active},
        message=f"Usuario {user.username} actualizado",
    )
    db.commit()
    return get_user(db, user.id)


def set_status(db: Session, actor: User, user_id: int, is_active: bool) -> User:
    user = get_user(db, user_id)
    if user is None:
        raise AppError("El usuario no existe.", 404)
    if user.id == actor.id and not is_active:
        raise AppError("No puedes desactivar tu propio usuario.")
    user.is_active = is_active
    user.updated_at = datetime.now(UTC)
    if not is_active:
        user.token_version += 1
    write_audit(
        db,
        user=actor,
        action="STATUS",
        entity="user",
        entity_id=user.id,
        parameters={"is_active": is_active},
        message=f"Usuario {user.username} {'activado' if is_active else 'desactivado'}",
    )
    db.commit()
    return get_user(db, user.id)

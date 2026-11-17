import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, User


SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "authorization"}


def sanitize(payload: dict | None) -> str | None:
    if payload is None:
        return None

    def clean(value):
        if isinstance(value, dict):
            return {key: ("***" if key.lower() in SENSITIVE_KEYS else clean(item)) for key, item in value.items()}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    return json.dumps(clean(payload), ensure_ascii=False, default=str)[:4000]


def write_audit(
    db: Session,
    *,
    user: User | None,
    action: str,
    entity: str = "",
    entity_id: str | int | None = None,
    tool_name: str | None = None,
    parameters: dict | None = None,
    result_status: str = "OK",
    message: str = "",
) -> None:
    db.add(
        AuditLog(
            user_id=None if user is None else user.id,
            action=action,
            entity=entity,
            entity_id=None if entity_id is None else str(entity_id),
            tool_name=tool_name,
            parameters_json=sanitize(parameters),
            result_status=result_status,
            message=message[:2000],
            created_at=datetime.now(UTC),
        )
    )


def list_audit(db: Session, page: int, page_size: int, action: str | None = None):
    query = select(AuditLog).order_by(AuditLog.id.desc())
    if action:
        query = query.where(AuditLog.action == action)
    total = db.query(AuditLog).count() if not action else db.query(AuditLog).filter(AuditLog.action == action).count()
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return total, rows

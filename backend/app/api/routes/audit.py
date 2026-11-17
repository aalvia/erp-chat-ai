from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import AuditLog, User
from app.schemas.dto import AuditOut, Page
from app.services.mappers import audit_out

router = APIRouter(prefix="/audit", tags=["Auditoría"])


@router.get("", response_model=Page)
def get_audit(
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("audit.read")),
):
    query = select(AuditLog).options(selectinload(AuditLog.user)).order_by(AuditLog.id.desc())
    if action:
        query = query.where(AuditLog.action == action)
    rows = db.scalars(query).all()
    total = len(rows)
    start = (page - 1) * page_size
    return Page(
        items=[audit_out(row) for row in rows[start : start + page_size]],
        total=total,
        page=page,
        page_size=page_size,
    )

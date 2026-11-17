from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import DashboardOut
from app.services.dashboard_service import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["Tablero"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("dashboard.read")),
):
    return build_dashboard(db, actor, date_from, date_to)

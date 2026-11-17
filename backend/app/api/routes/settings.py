from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import SettingsOut, SettingsUpdate
from app.services.audit_service import write_audit
from app.services.settings_service import get_company_settings, settings_out, update_settings

router = APIRouter(prefix="/settings", tags=["Configuración"])


@router.get("", response_model=SettingsOut)
def get_settings_route(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return settings_out(get_company_settings(db))


@router.put("", response_model=SettingsOut)
def put_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("settings.write")),
):
    row = update_settings(db, data)
    write_audit(
        db,
        user=actor,
        action="SETTINGS",
        entity="settings",
        entity_id=row.id,
        parameters={"tax_rate": str(data.tax_rate), "low_stock_threshold": data.low_stock_threshold},
        message="Configuración actualizada",
    )
    db.commit()
    return settings_out(row)

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CompanySetting, Inventory
from app.schemas.dto import SettingsOut, SettingsUpdate


def get_company_settings(db: Session) -> CompanySetting:
    row = db.get(CompanySetting, 1)
    if row is None:
        env = get_settings()
        row = CompanySetting(
            id=1,
            company_name="Horizonte Distribución",
            currency=env.currency,
            tax_rate=Decimal(env.tax_rate),
            low_stock_threshold=env.low_stock_threshold,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def settings_out(row: CompanySetting) -> SettingsOut:
    return SettingsOut(
        company_name=row.company_name,
        currency=row.currency,
        tax_rate=float(row.tax_rate),
        low_stock_threshold=row.low_stock_threshold,
    )


def update_settings(db: Session, data: SettingsUpdate) -> CompanySetting:
    row = get_company_settings(db)
    row.company_name = data.company_name.strip()
    row.tax_rate = Decimal(data.tax_rate)
    row.low_stock_threshold = data.low_stock_threshold
    now = datetime.now(UTC)
    for inventory in db.scalars(select(Inventory)).all():
        inventory.reorder_level = data.low_stock_threshold
        inventory.updated_at = now
    db.commit()
    db.refresh(row)
    return row

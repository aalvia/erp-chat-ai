import os

os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/intelligent_erp_test"
os.environ["JWT_SECRET"] = "test-secret-erp-local"
os.environ["JWT_EXPIRE_MINUTES"] = "60"

from app.config import get_settings

get_settings.cache_clear()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database.base import Base
from app.database.seed import DEMO_PASSWORD, seed_reference
from app.database.session import SessionLocal, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_reference(db)
    finally:
        db.close()
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_business():
    db = SessionLocal()
    db.execute(
        text(
            """
            TRUNCATE TABLE
                audit_logs,
                sale_details,
                sales,
                inventory_movements,
                inventory,
                products,
                categories,
                customers
            RESTART IDENTITY CASCADE
            """
        )
    )
    db.commit()
    db.close()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str = "admin") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": username, "password": DEMO_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

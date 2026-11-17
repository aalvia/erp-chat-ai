from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.models import Inventory, Sale
from tests.conftest import login


def _catalog(client, headers):
    category = client.post(
        "/api/products/categories",
        json={"name": "Oficina", "description": "Demo"},
        headers=headers,
    )
    assert category.status_code == 201, category.text
    product = client.post(
        "/api/products",
        json={
            "sku": "OF-001",
            "name": "Resma de papel",
            "description": "Papel",
            "category_id": category.json()["id"],
            "sale_price": "10.00",
            "cost": "4.00",
            "initial_quantity": 5,
        },
        headers=headers,
    )
    assert product.status_code == 201, product.text
    customer = client.post(
        "/api/customers",
        json={"identification": "900000111", "name": "Comercial Demo 01", "email": "c01@demo.local"},
        headers=headers,
    )
    assert customer.status_code == 201, customer.text
    return product.json(), customer.json()


def test_login_and_me(client):
    headers = login(client)
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "admin"
    assert "users.write" in body["permissions"]
    bad = client.post("/api/auth/login", json={"username": "admin", "password": "incorrecta1"})
    assert bad.status_code == 401


def test_seller_cannot_list_users(client):
    headers = login(client, "vendedor.ana")
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 403


def test_create_user_rejects_duplicate(client):
    headers = login(client)
    roles = client.get("/api/roles", headers=headers).json()
    seller = next(role for role in roles if role["code"] == "SELLER")
    payload = {
        "username": "vendedor.nuevo",
        "email": "nuevo@horizonte.demo",
        "full_name": "Vendedor Nuevo",
        "password": "Demo123!",
        "role_id": seller["id"],
    }
    created = client.post("/api/users", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    duplicated = client.post("/api/users", json=payload, headers=headers)
    assert duplicated.status_code == 409


def test_sale_updates_inventory_and_blocks_oversell(client, db):
    headers = login(client)
    product, customer = _catalog(client, headers)
    sale = client.post(
        "/api/sales",
        json={
            "customer_id": customer["id"],
            "sale_date": "2026-10-15",
            "notes": "Octubre",
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
        headers=headers,
    )
    assert sale.status_code == 201, sale.text
    assert sale.json()["total"] == 20
    stock = db.scalar(select(Inventory.quantity).where(Inventory.product_id == product["id"]))
    db.expire_all()
    stock = db.scalar(select(Inventory.quantity).where(Inventory.product_id == product["id"]))
    assert stock == 3
    denied = client.post(
        "/api/sales",
        json={
            "customer_id": customer["id"],
            "sale_date": "2026-10-16",
            "items": [{"product_id": product["id"], "quantity": 9}],
        },
        headers=headers,
    )
    assert denied.status_code == 409
    db.expire_all()
    stock = db.scalar(select(Inventory.quantity).where(Inventory.product_id == product["id"]))
    assert stock == 3
    count = db.scalar(select(func.count(Sale.id)))
    assert count == 1


def test_seller_only_sees_own_sales_and_reader_is_denied(client):
    admin = login(client)
    product, customer = _catalog(client, admin)
    seller = login(client, "vendedor.ana")
    created = client.post(
        "/api/sales",
        json={
            "customer_id": customer["id"],
            "sale_date": str(date.today()),
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
        headers=seller,
    )
    assert created.status_code == 201, created.text
    own = client.get("/api/sales", headers=seller)
    assert own.status_code == 200
    assert own.json()["total"] == 1
    reader = login(client, "consulta.sofia")
    denied = client.get("/api/sales", headers=reader)
    assert denied.status_code == 403


def test_dashboard_uses_database_totals(client, db):
    headers = login(client)
    product, customer = _catalog(client, headers)
    client.post(
        "/api/sales",
        json={
            "customer_id": customer["id"],
            "sale_date": "2026-10-02",
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
        headers=headers,
    )
    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    body = dashboard.json()
    total = db.scalar(select(func.coalesce(func.sum(Sale.total), 0)).where(Sale.status == "CONFIRMADA"))
    assert body["cantidad_ventas"] == 1
    assert Decimal(str(body["total_ventas"])) == Decimal(total)
    assert body["productos"] == 1
    assert body["clientes"] == 1

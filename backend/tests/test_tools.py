import pytest

from app.ai.ai_orchestrator import asks_all_sellers, handle_message, is_bulk_destructive
from app.ai.tool_executor import execute
from app.core.errors import AppError
from app.repositories.users import get_by_username
from tests.conftest import login


def _prepare(client):
    headers = login(client)
    category = client.post("/api/products/categories", json={"name": "Oficina", "description": "Demo"}, headers=headers)
    product = client.post(
        "/api/products",
        json={
            "sku": "OF-001",
            "name": "Resma de papel",
            "category_id": category.json()["id"],
            "sale_price": "10.00",
            "cost": "4.00",
            "initial_quantity": 20,
        },
        headers=headers,
    )
    other = client.post(
        "/api/products",
        json={
            "sku": "OF-002",
            "name": "Carpeta",
            "category_id": category.json()["id"],
            "sale_price": "3.00",
            "cost": "1.00",
            "initial_quantity": 4,
        },
        headers=headers,
    )
    customer = client.post(
        "/api/customers",
        json={"identification": "900000111", "name": "Comercial Demo 01"},
        headers=headers,
    )
    client.post(
        "/api/sales",
        json={
            "customer_id": customer.json()["id"],
            "sale_date": "2026-10-20",
            "items": [{"product_id": product.json()["id"], "quantity": 3}],
        },
        headers=headers,
    )
    client.post(
        "/api/sales",
        json={
            "customer_id": customer.json()["id"],
            "sale_date": "2026-11-02",
            "items": [{"product_id": other.json()["id"], "quantity": 1}],
        },
        headers=headers,
    )
    return headers


def test_sales_tool_matches_october(client, db):
    _prepare(client)
    admin = get_by_username(db, "admin")
    result = execute(
        db,
        admin,
        "consultar_ventas",
        {"fecha_inicio": "2026-10-01", "fecha_fin": "2026-10-31"},
    )
    assert result["data"]["cantidad"] == 1
    assert result["data"]["importe"] == 30


def test_top_product_and_low_stock(client, db):
    _prepare(client)
    admin = get_by_username(db, "admin")
    top = execute(
        db,
        admin,
        "consultar_top_productos",
        {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31", "limite": 1},
    )
    assert top["data"]["items"][0]["sku"] == "OF-001"
    low = execute(db, admin, "consultar_inventario", {"cantidad_menor_que": 10})
    skus = {item["sku"] for item in low["data"]["items"]}
    assert "OF-002" in skus
    assert "OF-001" not in skus


def test_obvious_routes_do_not_depend_on_a_wrong_intent():
    from app.ai.ai_orchestrator import route_override

    assert route_override("¿Dónde puedo crear un usuario?") == ("NAVIGATION", "buscar_funcionalidad_erp")
    assert route_override("¿Cómo registro una venta?") == ("HOW_TO", "consultar_documentacion")
    assert route_override("¿Cuál fue la temperatura promedio del océano en Marte?") == ("UNKNOWN", None)
    assert route_override("¿Cuántas ventas tuvimos durante octubre?") is None


def test_navigation_route_is_real(client, db):
    admin = get_by_username(db, "admin")
    result = execute(db, admin, "buscar_funcionalidad_erp", {"consulta": "¿Dónde puedo crear un usuario?"})
    assert result["actions"][0]["route"] == "/admin/users/new"
    assert len(result["actions"]) == 1


def test_reader_cannot_query_users_or_all_sellers(client, db):
    reader = get_by_username(db, "consulta.sofia")
    with pytest.raises(AppError):
        execute(db, reader, "consultar_usuarios", {})
    with pytest.raises(AppError):
        execute(db, reader, "ejecutar_sql", {"query": "select * from users"})
    response = handle_message(db, reader, "Muéstrame las ventas de todos los vendedores.", "sesion-prueba")
    assert "permiso" in response.message.lower()
    blocked = handle_message(db, reader, "Elimina todos los usuarios.", "sesion-prueba")
    assert blocked.intent == "ACTION"
    assert "no puedo" in blocked.message.lower()
    assert is_bulk_destructive("Elimina todos los usuarios.")
    assert asks_all_sellers("Muéstrame las ventas de todos los vendedores.")


def test_create_user_requires_confirmation(client, db):
    admin = get_by_username(db, "admin")
    staged = execute(
        db,
        admin,
        "crear_cliente",
        {"identificacion": "900000222", "nombre": "Comercial Demo 02"},
    )
    assert staged["data"]["pendiente"] is True
    token = staged["actions"][0]["confirmation_token"]
    from app.ai.tool_executor import confirm

    created = confirm(db, admin, token)
    assert created["nombre"] == "Comercial Demo 02"

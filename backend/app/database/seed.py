import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.permissions import PERMISSIONS, ROLE_DEFINITIONS, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models import Category, CompanySetting, Customer, Inventory, Permission, Product, Role, User
from app.schemas.dto import SaleCreate, SaleItemIn
from app.services.sales_service import create_sale
from app.services.settings_service import get_company_settings

DEMO_PASSWORD = "Demo123!"

REFERENCE_USERS = [
    ("admin", "admin@horizonte.demo", "Administrador Demo", "ADMIN"),
    ("vendedor.ana", "ana@horizonte.demo", "Ana Vendedora", "SELLER"),
    ("consulta.sofia", "sofia@horizonte.demo", "Sofia Consulta", "READER"),
]

DEMO_USERS = [
    ("admin", "admin@horizonte.demo", "Administrador Demo", "ADMIN"),
    ("vendedor.ana", "ana@horizonte.demo", "Ana Vendedora", "SELLER"),
    ("vendedor.luis", "luis@horizonte.demo", "Luis Vendedor", "SELLER"),
    ("vendedor.marta", "marta@horizonte.demo", "Marta Vendedora", "SELLER"),
    ("vendedor.carlos", "carlos@horizonte.demo", "Carlos Vendedor", "SELLER"),
    ("vendedor.julia", "julia@horizonte.demo", "Julia Vendedora", "SELLER"),
    ("consulta.sofia", "sofia@horizonte.demo", "Sofia Consulta", "READER"),
    ("consulta.diego", "diego@horizonte.demo", "Diego Consulta", "READER"),
    ("consulta.elena", "elena@horizonte.demo", "Elena Consulta", "READER"),
    ("consulta.pablo", "pablo@horizonte.demo", "Pablo Consulta", "READER"),
]

CATEGORIES = [
    ("Oficina", "Papelería y mobiliario de oficina"),
    ("Tecnología", "Equipos y accesorios"),
    ("Hogar", "Artículos para el hogar"),
    ("Ferretería", "Herramientas y fijaciones"),
    ("Abarrotes", "Productos secos de consumo"),
]

PRODUCTS = [
    ("OF-001", "Resma de papel carta", 0, "8.50", "5.10"),
    ("OF-002", "Carpeta de archivo", 0, "3.20", "1.40"),
    ("OF-003", "Bolígrafo azul caja", 0, "6.00", "2.80"),
    ("OF-004", "Grapadora metálica", 0, "9.75", "4.90"),
    ("OF-005", "Cinta adhesiva", 0, "2.40", "0.90"),
    ("OF-006", "Sobre manila paquete", 0, "7.10", "3.20"),
    ("OF-007", "Marcador permanente", 0, "4.30", "1.70"),
    ("OF-008", "Cuaderno empastado", 0, "5.60", "2.40"),
    ("TEC-001", "Mouse óptico", 1, "12.00", "6.50"),
    ("TEC-002", "Teclado USB", 1, "18.50", "9.40"),
    ("TEC-003", "Memoria USB 64GB", 1, "11.90", "6.10"),
    ("TEC-004", "Cable HDMI 2m", 1, "8.20", "3.40"),
    ("TEC-005", "Audífonos básicos", 1, "15.00", "7.20"),
    ("TEC-006", "Hub USB de 4 puertos", 1, "14.40", "6.80"),
    ("TEC-007", "Base para portátil", 1, "22.00", "11.50"),
    ("TEC-008", "Webcam HD", 1, "28.00", "14.00"),
    ("HOG-001", "Toalla de cocina par", 2, "9.00", "4.20"),
    ("HOG-002", "Vaso de vidrio caja", 2, "13.50", "6.70"),
    ("HOG-003", "Detergente líquido", 2, "6.80", "3.10"),
    ("HOG-004", "Bombillo LED", 2, "4.90", "2.10"),
    ("HOG-005", "Organizador plástico", 2, "10.50", "4.80"),
    ("HOG-006", "Escoba compacta", 2, "7.70", "3.40"),
    ("HOG-007", "Tendedero plegable", 2, "16.20", "8.10"),
    ("HOG-008", "Cesto de ropa", 2, "12.80", "6.00"),
    ("FER-001", "Martillo de uña", 3, "11.00", "5.50"),
    ("FER-002", "Destornillador estrella", 3, "4.60", "1.90"),
    ("FER-003", "Cinta métrica 5m", 3, "6.40", "2.70"),
    ("FER-004", "Juego de llaves", 3, "19.90", "10.20"),
    ("FER-005", "Tornillos surtidos", 3, "5.20", "2.10"),
    ("FER-006", "Alicate universal", 3, "8.90", "4.20"),
    ("FER-007", "Nivel de burbuja", 3, "9.40", "4.50"),
    ("FER-008", "Guantes de trabajo", 3, "7.30", "3.20"),
    ("ABA-001", "Arroz 5kg", 4, "8.10", "5.40"),
    ("ABA-002", "Frijol 2kg", 4, "6.50", "3.90"),
    ("ABA-003", "Aceite vegetal 1L", 4, "4.80", "2.90"),
    ("ABA-004", "Azúcar 2kg", 4, "3.90", "2.20"),
    ("ABA-005", "Café molido 500g", 4, "7.60", "4.40"),
    ("ABA-006", "Pasta 1kg", 4, "2.70", "1.40"),
    ("ABA-007", "Avena 1kg", 4, "3.40", "1.80"),
    ("ABA-008", "Sal 1kg", 4, "1.20", "0.50"),
]


def reset_tables(db: Session) -> None:
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
                customers,
                users,
                role_permissions,
                permissions,
                roles,
                company_settings
            RESTART IDENTITY CASCADE
            """
        )
    )
    db.commit()


def seed_reference(db: Session, users: list[tuple[str, str, str, str]] | None = None) -> None:
    users = users or REFERENCE_USERS
    permissions = {}
    for code, name, module, description in PERMISSIONS:
        permission = Permission(code=code, name=name, module=module, description=description)
        db.add(permission)
        permissions[code] = permission
    db.flush()
    roles = {}
    for code, name, description in ROLE_DEFINITIONS:
        role = Role(code=code, name=name, description=description)
        role.permissions = [permissions[item] for item in ROLE_PERMISSIONS[code]]
        db.add(role)
        roles[code] = role
    db.flush()
    password_hash = hash_password(DEMO_PASSWORD)
    now = datetime.now(UTC)
    for username, email, full_name, role_code in users:
        db.add(
            User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                role_id=roles[role_code].id,
                is_active=True,
                token_version=1,
                updated_at=now,
            )
        )
    db.add(
        CompanySetting(
            id=1,
            company_name="Horizonte Distribución",
            currency="USD",
            tax_rate=Decimal("0"),
            low_stock_threshold=10,
        )
    )
    db.commit()


def seed_demo(db: Session) -> dict:
    reset_tables(db)
    seed_reference(db, DEMO_USERS)
    settings = get_company_settings(db)
    categories = []
    for name, description in CATEGORIES:
        category = Category(name=name, description=description)
        db.add(category)
        categories.append(category)
    db.flush()
    products = []
    now = datetime.now(UTC)
    for sku, name, category_index, price, cost in PRODUCTS:
        product = Product(
            sku=sku,
            name=name,
            description=f"Producto de demostración {name}",
            category_id=categories[category_index].id,
            sale_price=Decimal(price),
            cost=Decimal(cost),
            is_active=True,
            updated_at=now,
        )
        db.add(product)
        db.flush()
        db.add(
            Inventory(
                product_id=product.id,
                quantity=180,
                reorder_level=settings.low_stock_threshold,
                updated_at=now,
            )
        )
        products.append(product)
    customers = []
    for index in range(1, 31):
        customer = Customer(
            identification=f"900{index:06d}",
            name=f"Comercial Demo {index:02d}",
            email=f"cliente{index:02d}@horizonte.demo",
            phone=f"300000{index:04d}",
            address=f"Calle {index} #10-20",
            is_active=True,
            updated_at=now,
        )
        db.add(customer)
        customers.append(customer)
    db.commit()
    sellers = list(db.scalars(select(User).join(User.role).where(Role.code == "SELLER")).all())
    rng = random.Random(42)
    start = date(2026, 1, 6)
    end = date(2026, 11, 15)
    span = (end - start).days
    created = 0
    for _ in range(130):
        seller = rng.choice(sellers)
        customer = rng.choice(customers)
        chosen = rng.sample(products, rng.randint(1, 3))
        items = []
        for product in chosen:
            inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id))
            quantity = rng.randint(1, 3)
            if inventory and inventory.quantity >= quantity:
                items.append(SaleItemIn(product_id=product.id, quantity=quantity))
        if not items:
            continue
        sale_date = start + timedelta(days=rng.randint(0, span))
        create_sale(
            db,
            seller,
            SaleCreate(customer_id=customer.id, sale_date=sale_date, notes="Venta de demostración", items=items),
        )
        created += 1
    low_targets = [2, 5, 9, 14]
    for product, quantity in zip(products[:4], low_targets):
        inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id))
        inventory.quantity = quantity
        inventory.updated_at = datetime.now(UTC)
    db.commit()
    return {"users": len(DEMO_USERS), "customers": len(customers), "products": len(products), "sales": created}

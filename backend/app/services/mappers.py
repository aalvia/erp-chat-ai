from decimal import Decimal

from app.models import AuditLog, Customer, InventoryMovement, Product, Role, Sale, User
from app.schemas.dto import (
    AuditOut,
    CustomerOut,
    MovementOut,
    ProductOut,
    RoleOut,
    SaleDetailOut,
    SaleOut,
    UserOut,
)


def as_float(value: Decimal | float | int) -> float:
    return float(Decimal(value).quantize(Decimal("0.01")))


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role_id=user.role_id,
        role_code=user.role.code,
        role_name=user.role.name,
        is_active=user.is_active,
        permissions=sorted(permission.code for permission in user.role.permissions),
    )


def role_out(role: Role) -> RoleOut:
    return RoleOut.model_validate(role)


def customer_out(customer: Customer) -> CustomerOut:
    return CustomerOut.model_validate(customer)


def product_out(product: Product) -> ProductOut:
    inventory = product.inventory
    return ProductOut(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        category_name=product.category.name,
        sale_price=as_float(product.sale_price),
        cost=as_float(product.cost),
        is_active=product.is_active,
        quantity=0 if inventory is None else inventory.quantity,
        reorder_level=0 if inventory is None else inventory.reorder_level,
    )


def movement_out(row: InventoryMovement) -> MovementOut:
    return MovementOut(
        id=row.id,
        product_id=row.product_id,
        product_name=row.product.name,
        sku=row.product.sku,
        movement_type=row.movement_type,
        quantity=row.quantity,
        previous_quantity=row.previous_quantity,
        new_quantity=row.new_quantity,
        reference_type=row.reference_type,
        reference_id=row.reference_id,
        notes=row.notes,
        user_name=None if row.user is None else row.user.full_name,
        created_at=row.created_at,
    )


def sale_out(sale: Sale, with_details: bool = False) -> SaleOut:
    details = []
    if with_details:
        details = [
            SaleDetailOut(
                id=detail.id,
                product_id=detail.product_id,
                sku=detail.product.sku,
                product_name=detail.product.name,
                quantity=detail.quantity,
                unit_price=as_float(detail.unit_price),
                line_total=as_float(detail.line_total),
            )
            for detail in sale.details
        ]
    return SaleOut(
        id=sale.id,
        number=sale.number,
        customer_id=sale.customer_id,
        customer_name=sale.customer.name,
        user_id=sale.user_id,
        user_name=sale.user.full_name,
        status=sale.status,
        subtotal=as_float(sale.subtotal),
        tax_rate=as_float(sale.tax_rate),
        tax_amount=as_float(sale.tax_amount),
        total=as_float(sale.total),
        sale_date=sale.sale_date,
        notes=sale.notes,
        details=details,
    )


def audit_out(row: AuditLog) -> AuditOut:
    return AuditOut(
        id=row.id,
        user_id=row.user_id,
        user_name=None if row.user is None else row.user.full_name,
        action=row.action,
        entity=row.entity,
        entity_id=row.entity_id,
        tool_name=row.tool_name,
        result_status=row.result_status,
        message=row.message,
        created_at=row.created_at,
    )

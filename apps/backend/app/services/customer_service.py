"""Customer record service helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.enums import CustomerStatus
from app.schemas.customers import CustomerCreate, CustomerUpdate


class CustomerNotFoundError(Exception):
    """Raised when a customer is missing in the requested workspace."""


async def list_customers(
    session: AsyncSession,
    workspace_id: UUID,
    *,
    search: str | None = None,
    status: CustomerStatus | None = None,
) -> list[Customer]:
    """List customers in a workspace with optional search and status filters."""
    query = select(Customer).where(Customer.workspace_id == workspace_id)

    if status is not None:
        query = query.where(Customer.status == status)

    if search is not None:
        trimmed = search.strip()
        if trimmed:
            pattern = f"%{trimmed}%"
            query = query.where(
                or_(
                    Customer.display_name.ilike(pattern),
                    Customer.email.ilike(pattern),
                    Customer.phone.ilike(pattern),
                    Customer.external_id.ilike(pattern),
                ),
            )

    query = query.order_by(Customer.display_name.asc())
    result = await session.scalars(query)
    return list(result.all())


async def get_customer(
    session: AsyncSession,
    workspace_id: UUID,
    customer_id: UUID,
) -> Customer | None:
    """Return a customer scoped to the workspace, if it exists."""
    return await session.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.workspace_id == workspace_id,
        ),
    )


async def create_customer(
    session: AsyncSession,
    workspace_id: UUID,
    data: CustomerCreate,
) -> Customer:
    """Create a customer in the workspace."""
    customer = Customer(
        workspace_id=workspace_id,
        display_name=data.display_name,
        email=data.email,
        phone=data.phone,
        external_id=data.external_id,
        locale=data.locale,
        notes=data.notes,
        status=data.status or CustomerStatus.ACTIVE,
    )
    session.add(customer)
    await session.flush()
    return customer


async def update_customer(
    session: AsyncSession,
    workspace_id: UUID,
    customer_id: UUID,
    data: CustomerUpdate,
) -> Customer:
    """Update a customer in the workspace."""
    customer = await get_customer(session, workspace_id, customer_id)
    if customer is None:
        raise CustomerNotFoundError("Customer not found")

    if "display_name" in data.model_fields_set:
        customer.display_name = data.display_name
    if "email" in data.model_fields_set:
        customer.email = data.email
    if "phone" in data.model_fields_set:
        customer.phone = data.phone
    if "external_id" in data.model_fields_set:
        customer.external_id = data.external_id
    if "locale" in data.model_fields_set:
        customer.locale = data.locale
    if "notes" in data.model_fields_set:
        customer.notes = data.notes
    if "status" in data.model_fields_set and data.status is not None:
        customer.status = data.status

    await session.flush()
    return customer


async def archive_customer(
    session: AsyncSession,
    workspace_id: UUID,
    customer_id: UUID,
) -> Customer:
    """Archive a customer in the workspace."""
    customer = await get_customer(session, workspace_id, customer_id)
    if customer is None:
        raise CustomerNotFoundError("Customer not found")

    customer.status = CustomerStatus.ARCHIVED
    await session.flush()
    return customer


async def delete_customer(
    session: AsyncSession,
    workspace_id: UUID,
    customer_id: UUID,
) -> UUID:
    """Hard-delete a customer from the workspace."""
    customer = await get_customer(session, workspace_id, customer_id)
    if customer is None:
        raise CustomerNotFoundError("Customer not found")

    customer_id_value = customer.id
    await session.delete(customer)
    await session.flush()
    return customer_id_value

"""Workspace customer record API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.workspace_deps import get_active_workspace_membership
from app.db.session import get_async_session
from app.models.enums import CustomerStatus
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.customers import (
    CustomerCreate,
    CustomerDeleteRead,
    CustomerRead,
    CustomerUpdate,
)
from app.services.customer_service import (
    CustomerNotFoundError,
    create_customer,
    delete_customer,
    get_customer,
    list_customers,
    update_customer,
)

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/customers",
    tags=["customers"],
)

DUPLICATE_CUSTOMER_EMAIL_MESSAGE = "Customer email already exists in this workspace"
DUPLICATE_CUSTOMER_EXTERNAL_ID_MESSAGE = (
    "Customer external ID already exists in this workspace"
)


def _envelope(data: dict | list) -> dict:
    return {"data": data, "meta": {}, "error": None}


def _map_integrity_error(exc: IntegrityError) -> HTTPException:
    message = str(getattr(exc, "orig", exc))
    if "uq_customers_workspace_id_email" in message:
        detail = DUPLICATE_CUSTOMER_EMAIL_MESSAGE
    elif "uq_customers_workspace_id_external_id" in message:
        detail = DUPLICATE_CUSTOMER_EXTERNAL_ID_MESSAGE
    else:
        detail = "Customer data conflicts with an existing record"
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail,
    )


@router.get("")
async def list_workspace_customers(
    workspace_id: UUID,
    search: str | None = Query(default=None),
    status: CustomerStatus | None = Query(default=None),
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List customers in the workspace."""
    _ = membership
    items = await list_customers(
        session,
        workspace_id,
        search=search,
        status=status,
    )
    return _envelope(
        [
            CustomerRead.model_validate(item).model_dump(mode="json")
            for item in items
        ],
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace_customer(
    body: CustomerCreate,
    workspace_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a customer in the workspace."""
    _ = membership
    try:
        customer = await create_customer(session, workspace_id, body)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise _map_integrity_error(exc) from exc
    await session.refresh(customer)
    return _envelope(CustomerRead.model_validate(customer).model_dump(mode="json"))


@router.get("/{customer_id}")
async def get_workspace_customer(
    workspace_id: UUID,
    customer_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get a customer by id in the workspace."""
    _ = membership
    customer = await get_customer(session, workspace_id, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return _envelope(CustomerRead.model_validate(customer).model_dump(mode="json"))


@router.patch("/{customer_id}")
async def update_workspace_customer(
    body: CustomerUpdate,
    workspace_id: UUID,
    customer_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update a customer in the workspace."""
    _ = membership
    try:
        customer = await update_customer(session, workspace_id, customer_id, body)
        await session.commit()
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        ) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise _map_integrity_error(exc) from exc
    await session.refresh(customer)
    return _envelope(CustomerRead.model_validate(customer).model_dump(mode="json"))


@router.delete("/{customer_id}")
async def delete_workspace_customer(
    workspace_id: UUID,
    customer_id: UUID,
    membership: WorkspaceMembership = Depends(get_active_workspace_membership),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Hard-delete a customer from the workspace."""
    _ = membership
    try:
        deleted_id = await delete_customer(session, workspace_id, customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        ) from exc

    await session.commit()
    return _envelope(
        CustomerDeleteRead(id=deleted_id, deleted=True).model_dump(mode="json"),
    )

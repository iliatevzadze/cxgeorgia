"""Tests for customer model metadata and persistence."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import UniqueConstraint

import app.models  # noqa: F401 — ensure models are registered
from app.db.base import Base
from app.models.customer import Customer
from app.models.enums import CustomerStatus, UserStatus, WorkspaceStatus
from app.models.user import User
from app.models.workspace import Workspace


def _column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def _foreign_key_targets(table_name: str, column_name: str) -> set[str]:
    column = Base.metadata.tables[table_name].c[column_name]
    return {fk.column.table.name for fk in column.foreign_keys}


def _unique_column_sets(table_name: str) -> set[tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    unique_sets: set[tuple[str, ...]] = set()
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            unique_sets.add(tuple(column.name for column in constraint.columns))
    for index in table.indexes:
        if index.unique:
            unique_sets.add(tuple(column.name for column in index.columns))
    return unique_sets


def test_customers_columns() -> None:
    assert _column_names("customers") == {
        "id",
        "workspace_id",
        "display_name",
        "email",
        "phone",
        "external_id",
        "locale",
        "notes",
        "status",
        "created_at",
        "updated_at",
    }


def test_customers_workspace_fk() -> None:
    assert _foreign_key_targets("customers", "workspace_id") == {"workspaces"}


def test_customers_indexes_and_unique_constraints() -> None:
    indexes = Base.metadata.tables["customers"].indexes
    index_columns = {tuple(index.columns.keys()) for index in indexes}
    assert ("workspace_id",) in index_columns
    assert ("email",) in index_columns
    unique_sets = _unique_column_sets("customers")
    assert ("workspace_id", "email") in unique_sets
    assert ("workspace_id", "external_id") in unique_sets


def test_workspace_customers_relationship() -> None:
    assert Customer.workspace.property.back_populates == "customers"
    assert Workspace.customers.property.back_populates == "workspace"


async def _create_workspace(db_session: AsyncSession) -> Workspace:
    suffix = uuid.uuid4().hex[:12]
    workspace = Workspace(
        name=f"Customer Workspace {suffix}",
        slug=f"customer-workspace-{suffix}",
        status=WorkspaceStatus.ACTIVE,
    )
    user = User(
        email=f"customer-user-{suffix}@example.com",
        password_hash="hashed-password",
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([workspace, user])
    await db_session.flush()
    return workspace


@pytest.mark.asyncio
async def test_customer_required_fields(db_session: AsyncSession) -> None:
    workspace = await _create_workspace(db_session)

    customer = Customer(
        workspace_id=workspace.id,
        display_name="Nino Beridze",
        email="nino@example.com",
        status=CustomerStatus.ACTIVE,
    )
    db_session.add(customer)
    await db_session.flush()
    await db_session.refresh(customer)

    assert customer.id is not None
    assert customer.workspace_id == workspace.id
    assert customer.display_name == "Nino Beridze"
    assert customer.email == "nino@example.com"
    assert customer.status == CustomerStatus.ACTIVE
    assert customer.created_at is not None
    assert customer.updated_at is not None


@pytest.mark.asyncio
async def test_duplicate_email_in_same_workspace_is_rejected(
    db_session: AsyncSession,
) -> None:
    workspace = await _create_workspace(db_session)

    first = Customer(
        workspace_id=workspace.id,
        display_name="First Customer",
        email="shared@example.com",
    )
    db_session.add(first)
    await db_session.flush()

    duplicate = Customer(
        workspace_id=workspace.id,
        display_name="Second Customer",
        email="shared@example.com",
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_same_email_in_different_workspaces_is_allowed(
    db_session: AsyncSession,
) -> None:
    workspace_a = await _create_workspace(db_session)
    workspace_b = await _create_workspace(db_session)

    customer_a = Customer(
        workspace_id=workspace_a.id,
        display_name="Customer A",
        email="shared@example.com",
    )
    customer_b = Customer(
        workspace_id=workspace_b.id,
        display_name="Customer B",
        email="shared@example.com",
    )
    db_session.add_all([customer_a, customer_b])
    await db_session.flush()

    assert customer_a.id is not None
    assert customer_b.id is not None
    assert customer_a.id != customer_b.id


@pytest.mark.asyncio
async def test_duplicate_external_id_in_same_workspace_is_rejected(
    db_session: AsyncSession,
) -> None:
    workspace = await _create_workspace(db_session)

    first = Customer(
        workspace_id=workspace.id,
        display_name="First Customer",
        external_id="crm-100",
    )
    db_session.add(first)
    await db_session.flush()

    duplicate = Customer(
        workspace_id=workspace.id,
        display_name="Second Customer",
        external_id="crm-100",
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_deleting_workspace_removes_customers(db_session: AsyncSession) -> None:
    workspace = await _create_workspace(db_session)

    customer = Customer(
        workspace_id=workspace.id,
        display_name="Workspace scoped",
    )
    db_session.add(customer)
    await db_session.flush()
    customer_id = customer.id

    await db_session.delete(workspace)
    await db_session.flush()

    assert await db_session.get(Customer, customer_id) is None


@pytest.mark.asyncio
async def test_archive_customer_sets_status(db_session: AsyncSession) -> None:
    from app.services.customer_service import archive_customer

    workspace = await _create_workspace(db_session)

    customer = Customer(
        workspace_id=workspace.id,
        display_name="Archive Me",
        status=CustomerStatus.ACTIVE,
    )
    db_session.add(customer)
    await db_session.flush()

    archived = await archive_customer(db_session, workspace.id, customer.id)
    assert archived.status == CustomerStatus.ARCHIVED

    refreshed = await db_session.scalar(
        select(Customer).where(Customer.id == customer.id),
    )
    assert refreshed is not None
    assert refreshed.status == CustomerStatus.ARCHIVED

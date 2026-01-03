import pytest
from db.connector import AsyncSession

from repositories.storages import get_storage_for_new_file_by_user


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_returns_storage_when_can_add_true(created_storage_with_upload, user_id):
    async with AsyncSession() as session:
        found = await get_storage_for_new_file_by_user(session=session, user_id=user_id)

    assert found is not None
    assert found.id == created_storage_with_upload.id
    assert found.can_add is True


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations', 'created_storage')
async def test_returns_none_when_no_can_add(user_id):
    async with AsyncSession() as session:
        found = await get_storage_for_new_file_by_user(session=session, user_id=user_id)

    assert found is None


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_returns_the_one_with_can_add_true_when_mixed(storages_mixed, user_id):
    storage_can, storage_cant = storages_mixed

    async with AsyncSession() as session:
        found = await get_storage_for_new_file_by_user(session=session, user_id=user_id)

    assert found is not None
    assert found.id == storage_can.id  # благодаря order_by(created_at.asc()) — зависит от времени создания
    assert found.can_add is True


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_returns_none_when_no_storages_at_all(user_id):
    async with AsyncSession() as session:
        found = await get_storage_for_new_file_by_user(session=session, user_id=user_id)

    assert found is None

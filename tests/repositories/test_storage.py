import uuid

import pytest

from db.connector import AsyncSession
from db.models import Storage
from repositories.storages import create_storage, delete_storage, get_storage_by_id, update_storage


@pytest.mark.usefixtures('apply_migrations')
async def test_create_storage(faker):
    storage = Storage(
        user_id=uuid.uuid4(),
        name=faker.word(),
        path=faker.word(),
        created_by=uuid.uuid4(),
    )
    async with AsyncSession() as session:
        await create_storage(session=session, new_storage=storage)
        await session.commit()
    assert storage.id is not None


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_storage_by_id(created_storage):
    async with AsyncSession() as session:
        storage = await get_storage_by_id(session=session, storage_id=created_storage.id)
    assert storage.user_id == created_storage.user_id
    assert storage.name == created_storage.name


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_update_storage(created_storage):
    update_data = {
        'name': 'new_name',
        'path': 'new_path',
    }
    async with AsyncSession() as session:
        updated_storage = await update_storage(
            session=session, storage_id=created_storage.id, update_data=update_data
        )
    assert updated_storage.name == update_data['name']
    assert updated_storage.path == update_data['path']


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_delete_storage(created_storage):
    async with AsyncSession() as session:
        result = await delete_storage(session=session, storage_id=created_storage.id)
        assert result == 1

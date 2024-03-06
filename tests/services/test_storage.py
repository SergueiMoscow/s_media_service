import uuid

import pytest
from sqlalchemy import select

from common.exceptions import InvalidKey
from common.settings import settings
from db import models
from db.connector import AsyncSession
from schemas.storage import CreateStorage, StorageUpdate
from services.storages import (
    create_storage_service,
    delete_storage_service,
    get_list_storages_service,
    get_storage_by_id_service,
    update_storage_service,
)


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_create_storage_service_success(faker):
    key = settings.KEY
    new_storage = CreateStorage(
        key=key,
        user_id=uuid.uuid4(),
        name=faker.word(),
        path=faker.word(),
        created_by=uuid.uuid4(),
    )
    storage = await create_storage_service(new_storage)
    async with AsyncSession() as session:
        inserted_storage = (
            await session.scalars(select(models.Storage).where(models.Storage.id == storage.id))
        ).first()
        assert inserted_storage.user_id == storage.user_id


async def test_create_storage_service_wrong_key(faker):
    key = 'test wrong key' + faker.word()
    new_storage = CreateStorage(
        key=key,
        user_id=uuid.uuid4(),
        name=faker.word(),
        path=faker.word(),
        created_by=uuid.uuid4(),
    )
    with pytest.raises(InvalidKey):
        await create_storage_service(new_storage)


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_storage_by_id(created_storage):
    storage = await get_storage_by_id_service(storage_id=created_storage.id)
    assert storage.user_id == created_storage.user_id
    assert storage.name == created_storage.name


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_update_storage(created_storage):
    update_data = StorageUpdate(
        user_id=created_storage.user_id,
        name='new name',
        path='/new/path',
        key=settings.KEY,
    )
    storage = await update_storage_service(storage_id=created_storage.id, update_data=update_data)
    assert storage.name == update_data.name
    assert storage.path == update_data.path


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_delete_storage(created_storage):
    result = await delete_storage_service(storage_id=created_storage.id)
    assert result == 1


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations', 'created_storage')
async def test_get_list_storages():
    result = await get_list_storages_service()
    assert result is not None
    assert len(result) == 1

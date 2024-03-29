import uuid
from typing import Optional

from common.exceptions import BadRequest, InvalidKey, NotAllowed, NotFound
from common.settings import settings
from db.connector import AsyncSession
from db.models import Storage
from repositories.storages import (
    create_storage,
    delete_storage,
    get_list_storages,
    get_storage_by_id,
    update_storage,
)
from schemas.storage import CreateStorage, StorageUpdate


async def create_storage_service(new_storage: CreateStorage) -> Storage:
    if new_storage.key != settings.KEY:
        raise InvalidKey
    storage = Storage(
        user_id=new_storage.user_id,
        name=new_storage.name,
        path=new_storage.path,
        created_by=new_storage.created_by,
    )
    async with AsyncSession() as session:
        await create_storage(session=session, new_storage=storage)
        await session.commit()
    if storage.id is None:
        raise BadRequest(error_code='cant_create_storage', error_message="Can't create storage")
    return storage


async def get_storage_by_id_service(storage_id: uuid) -> Storage:
    async with AsyncSession() as session:
        storage = await get_storage_by_id(session=session, storage_id=storage_id)
        return storage


async def update_storage_service(storage_id: uuid, update_data: StorageUpdate) -> Storage:
    if update_data.key != settings.KEY:
        raise InvalidKey
    async with AsyncSession() as session:
        storage = await get_storage_by_id(session=session, storage_id=storage_id)
        if storage is None:
            raise NotFound(error_code='not_found', error_message=f'Storage {storage_id} not found')
        if update_data.user_id != storage.user_id:
            raise NotAllowed(
                error_code='not_allowed',
                error_message=f'Storage {storage_id} is not allowed for user {update_data.user_id}',
            )

        return await update_storage(session, storage_id, update_data.model_dump())


async def delete_storage_service(storage_id: uuid) -> int:
    # TO_DO: Сделать проверку, что удаляет либо owner, либо по правильному ключу
    async with AsyncSession() as session:
        result = await delete_storage(session=session, storage_id=storage_id)
        return result


async def get_list_storages_service(user_id: Optional[uuid] = None) -> list[Storage]:
    async with AsyncSession() as session:
        result = await get_list_storages(session=session, user_id=user_id)
        return result

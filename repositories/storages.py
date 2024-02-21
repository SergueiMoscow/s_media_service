import uuid
from typing import Optional

from sqlalchemy import delete, select

from db import models
from db.connector import AsyncSession
from db.models import Storage


async def create_storage(session: AsyncSession, new_storage: Storage) -> Storage:
    session.add(new_storage)
    return new_storage


async def get_storage_by_id(session: AsyncSession, storage_id: uuid) -> Storage:
    storage = await session.scalar(select(models.Storage).where(models.Storage.id == storage_id))
    return storage


async def get_list_storages(session: AsyncSession, user_id: Optional[uuid] = None) -> list[Storage]:
    if user_id:
        result = await session.execute(select(Storage).where(Storage.user_id == user_id))
    else:
        result = await session.execute(select(Storage))
    return result.scalars().all()


async def update_storage(
    session: AsyncSession, storage_id: uuid, update_data: dict
) -> Storage | None:
    storage = await session.scalar(select(models.Storage).where(Storage.id == storage_id))
    if not storage:
        return None
    for key, value in update_data.items():
        setattr(storage, key, value)
    await session.commit()
    return storage


async def delete_storage(session: AsyncSession, storage_id: uuid) -> int:
    storage = await get_storage_by_id(session, storage_id)
    if storage:
        result = await session.execute(
            delete(models.Storage).where(models.Storage.id == storage_id)
        )
        await session.commit()
        return result.rowcount
    return 0


async def find_storage_by_path(session, full_path: str) -> Optional[Storage]:
    full_path_parts = full_path.split("/")
    for i in range(len(full_path_parts), 0, -1):
        path = "/".join(full_path_parts[:i])
        statement = select(Storage).filter((Storage.path == path) | (Storage.path == path+"/"))
        result = await session.execute(statement)
        storage = result.scalars().first()
        if storage is not None:
            return storage
    return None

import uuid

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

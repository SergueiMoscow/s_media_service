import uuid

from db.connector import AsyncSession
from repositories.storages import get_list_storages
from schemas.storage import StorageFolder
from services.storage_manager import StorageManager


async def get_storages_summary(user_id: uuid.UUID) -> list[StorageFolder]:
    with AsyncSession() as session:
        storages = await get_list_storages(session=session, user_id=user_id)
        results = []
        for storage in storages:
            storage_manager = StorageManager(storage.path)
            results.append(await storage_manager.get_storage_summary())
        return results

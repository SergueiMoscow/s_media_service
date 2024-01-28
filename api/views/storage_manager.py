import uuid

from fastapi import APIRouter

from schemas.storage import StorageFolder
from services.storage_manager import OrderStorage, StorageManager
from services.storages import get_storage_by_id_service

router = APIRouter(prefix='/storage')


@router.get('/{storage_id}')
async def get_storage_content(storage_id: uuid.UUID, order_by: OrderStorage) -> StorageFolder:
    storage = await get_storage_by_id_service(storage_id)
    storage_content = StorageManager(storage.path)
    return await storage_content.get_storage_content(order_by)


@router.get('/')
async def get_storages_summary(user_id: uuid.UUID) -> list[StorageFolder]:
    storages_content = await get_storages_summary(user_id)
    return storages_content

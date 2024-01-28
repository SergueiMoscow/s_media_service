import uuid

from fastapi import APIRouter

from schemas.storage import StorageFolder
from services.storage_manager import StorageManager, OrderStorage
from services.storages import get_storage_by_id_service

router = APIRouter(prefix='/storage')


@router.get('/{storage_id}')
async def get_storage_content(storage_id: uuid.UUID, order_by: OrderStorage) -> StorageFolder:
    storage = await get_storage_by_id_service(storage_id)
    storage_content = StorageManager(storage.path)
    return await storage_content.get_storage_content(order_by)

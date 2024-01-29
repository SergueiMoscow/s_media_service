import uuid

from fastapi import APIRouter

from common.exceptions import BadRequest
from schemas.storage import StorageFolder, StorageSummaryResponse
from services.storage_content import get_storages_summary_service
from services.storage_manager import OrderFolder, StorageManager
from services.storages import get_storage_by_id_service

router = APIRouter(prefix='/storage')


@router.get('/{storage_id}')
async def get_storage_content(storage_id: uuid.UUID, order_by: OrderFolder) -> StorageFolder:
    storage = await get_storage_by_id_service(storage_id)
    storage_content = StorageManager(storage.path)
    return await storage_content.get_storage_content(order_by)


@router.get('/')
async def get_storages_summary(user_id: uuid.UUID) -> StorageSummaryResponse:
    try:
        storages_content = await get_storages_summary_service(user_id)
    except FileNotFoundError as e:
        raise BadRequest from e
    return StorageSummaryResponse(results=storages_content)

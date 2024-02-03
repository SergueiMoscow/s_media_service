import io
import uuid

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from common.exceptions import BadRequest
from schemas.storage import StorageFolder, StorageSummaryResponse, FolderContentResponse
from services.storage_content import get_storage_collage_service, get_storages_summary_service
from services.storage_manager import PAGE_SIZE, OrderFolder, StorageManager
from services.storages import get_storage_by_id_service

router = APIRouter(prefix='/storage')


@router.get('/{storage_id}')
async def get_storage_content(
    storage_id: uuid.UUID,
    folder: str = '',
    page_number: int = 1,
    page_size: int = PAGE_SIZE,
    order_by: OrderFolder = OrderFolder.NAME,
) -> FolderContentResponse:
    storage = await get_storage_by_id_service(storage_id)
    storage_content = StorageManager(
        storage=storage, storage_path=folder, page_number=page_number, page_size=page_size
    )
    results = await storage_content.get_storage_content(order_by)
    return FolderContentResponse(results=results)


@router.get('/')
async def get_storages_summary(user_id: uuid.UUID) -> StorageSummaryResponse:
    try:
        storages_content = await get_storages_summary_service(user_id)
    except FileNotFoundError as e:
        raise BadRequest from e
    return StorageSummaryResponse(results=storages_content)


@router.get('/collage/{storage_id}')
async def get_storage_collage(storage_id: uuid.UUID, folder: str) -> StreamingResponse:
    collage_image = await get_storage_collage_service(
        storage_id=storage_id,
        folder=folder,
    )
    return StreamingResponse(io.BytesIO(collage_image), media_type='image/png')

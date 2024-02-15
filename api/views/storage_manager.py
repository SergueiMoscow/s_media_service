import io
import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse

from common.exceptions import BadRequest
from schemas.storage import FolderContentResponse, StorageSummaryResponse
from services.storage_content import get_storage_collage_service, get_storages_summary_service
from services.storage_file import get_storage_file_service
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
    try:
        results = await storage_content.get_storage_folder_content(order_by)
    except Exception:
        pass
    return FolderContentResponse(results=results)


@router.get('/')
async def get_storages_summary(user_id: uuid.UUID) -> StorageSummaryResponse:
    try:
        storages_content = await get_storages_summary_service(user_id)
    except FileNotFoundError as e:
        raise BadRequest from e
    except Exception:
        pass
    return StorageSummaryResponse(results=storages_content)


@router.get('/collage/{storage_id}')
async def get_storage_collage(storage_id: uuid.UUID, folder: str) -> StreamingResponse:
    try:
        collage_image = await get_storage_collage_service(
            storage_id=storage_id,
            folder=folder,
        )
    except ValueError as e:
        raise BadRequest(error_code='400', error_message=e.args[0])
    except Exception:
        pass
    return StreamingResponse(io.BytesIO(collage_image), media_type='image/png')


@router.get('/file/{storage_id}')
async def get_file(
    storage_id: uuid.UUID, folder: str, filename: str, width: int | None = None
) -> FileResponse:
    # try:
    return await get_storage_file_service(
        storage_id=storage_id, folder=folder, filename=filename, width=width
    )
    # except Exception as e:
    #     print(e)


# @router.get('/file/{storage_id}')
# async def get_file(storage_id: uuid.UUID, folder: str, filename: str, width: int = 800)
# -> StreamingResponse:
#     try:
#         storage = await get_storage_by_id_service(storage_id=storage_id)
#         storage_path = pathlib.Path(storage.path) / folder
#         return await get_resized_image(storage_path, filename, max_width=width)
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=404, detail="File not found")

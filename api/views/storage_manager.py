import io
import logging
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse

from common.exceptions import BadRequest
from common.utils import get_header_user_id
from schemas.catalog import CatalogFileRequest, CatalogFileResponse
from schemas.storage import FolderContentResponse, StorageSummaryResponse, Pagination
from services.catalog import file_add_data_service
from services.collage_maker import CollageMaker
from services.storage_content import get_storage_collage_service, get_storages_summary_service
from services.storage_file import get_storage_file_service
from services.storage_manager import PAGE_SIZE, OrderFolder, StorageManager
from services.storages import get_storage_by_id_service

router = APIRouter(prefix='/storage')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)


@router.get('/{storage_id}')
async def get_storage_content(
    storage_id: uuid.UUID,
    folder: str = '',
    page: int = 1,
    page_size: int = PAGE_SIZE,
    order_by: OrderFolder = OrderFolder.NAME,
) -> FolderContentResponse:
    storage = await get_storage_by_id_service(storage_id)
    storage_content = StorageManager(
        storage=storage, storage_path=folder, order_by=order_by, page_number=page, page_size=page_size
    )
    # try:
    results = await storage_content.get_storage_folder_content()
    pagination = Pagination(
        page=page,
        per_page=page_size,
        items=results.folders_count.direct + results.files_count.direct,
    )
    # except Exception as e:
    #     logger.error(f"Storage Manager get_storage_content Exception: {e}")
    return FolderContentResponse(results=results, pagination=pagination)


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
    except Exception as e:
        logger.error(f"Storage Manager get_storage_collage Exception: {e}")
        collage_image = CollageMaker.generate_image_with_text(text=str(e))
    return StreamingResponse(io.BytesIO(collage_image), media_type='image/png')


@router.get('/preview/{storage_id}')
async def get_file(
    storage_id: uuid.UUID, folder: str, filename: str, width: int | None = None
) -> FileResponse:
    # try:
    return await get_storage_file_service(
        storage_id=storage_id, folder=folder, filename=filename, width=width, preview=True,
    )
    # except Exception as e:
    #     print(e)


@router.get('/file/{storage_id}')
async def get_file(
    storage_id: uuid.UUID, folder: str, filename: str, width: int | None = None
) -> FileResponse:
    # try:
    return await get_storage_file_service(
        storage_id=storage_id, folder=folder, filename=filename, width=width, preview=False,
    )
    # except Exception as e:
    #     print(e)


@router.post('/fileinfo')
async def add_or_change_data(
    data: CatalogFileRequest, user_id: uuid.UUID = Depends(get_header_user_id)
) -> CatalogFileResponse:
    try:
        data.user_id = user_id
        result = await file_add_data_service(data)
    except FileNotFoundError as e:
        raise BadRequest(error_code='file_not_found', error_message=str(e)) from e
    return CatalogFileResponse(result=result)


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

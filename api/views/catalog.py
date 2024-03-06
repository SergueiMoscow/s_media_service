"""
Методы для работы с моделью File
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import FileResponse, JSONResponse

from common.settings import settings
from common.utils import get_header_user_id
from schemas.catalog import CatalogFileRequest, CatalogFileResponse, ListCatalogFilesResponse
from services.catalog import (
    file_add_data_service,
    get_catalog_file_service,
    get_items_for_main_page_service,
    get_user_tags_service,
)

router = APIRouter(prefix='/catalog')


@router.post('')
async def add_or_change_data(data: CatalogFileRequest) -> CatalogFileResponse:
    result = await file_add_data_service(data)
    return CatalogFileResponse(result=result)


@router.get('/tags')
async def get_user_tags(user_id: uuid.UUID = Depends(get_header_user_id)):
    result = await get_user_tags_service(user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content={'results': result})


@router.get('/main')
async def get_images_for_main_page(
    page: int = 1, per_page: int = settings.PER_PAGE, created_before: datetime = None
) -> ListCatalogFilesResponse:
    return await get_items_for_main_page_service(
        page=page, per_page=per_page, created_before=created_before
    )


@router.get('/preview/{file_id}')
async def get_file(file_id: uuid.UUID, width: int | None = None) -> FileResponse:
    # try:
    return await get_catalog_file_service(file_id=file_id, width=width)
    # except Exception as e:
    #     print(e)

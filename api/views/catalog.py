"""
Методы для работы с моделью File
"""
import uuid
from datetime import datetime
from typing import List, Annotated

from fastapi import APIRouter, Depends, Query
from starlette import status
from starlette.responses import FileResponse, JSONResponse

from common.settings import settings
from common.utils import get_header_user_id
from schemas.catalog import (
    CatalogContentRequest,
    CatalogFileRequest,
    CatalogFileResponse,
    ListCatalogFilesResponse, ListCatalogFilesResponseWithPagination,
)
from services.catalog import (
    ListCatalogFileResponse,
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


@router.get('/preview/{id}')
async def get_file(id: uuid.UUID, width: int | None = None) -> FileResponse:
    # try:
    if width is None:
        width = settings.PREVIEW_WIDTH
    return await get_catalog_file_service(file_id=id, width=width)
    # except Exception as e:
    #     print(e)


@router.get('/content')
async def catalog_content(
    storage_id: uuid.UUID,
    tags: Annotated[list[str], Query()] = (),
    params: CatalogContentRequest = Depends(CatalogContentRequest)
):
    def split_query_param(value: str = Query("")) -> List[str]:
        return value.split(",") if value else []

    if len(tags) == 1 and ',' in tags[0]:
        params.tags = split_query_param(tags[0])
    else:
        params.tags = tags
    files, pagination = await ListCatalogFileResponse().get_files(storage_id, params)
    return ListCatalogFilesResponseWithPagination(
        files=files,
        pagination=pagination,
        status_code=status.HTTP_200_OK,
    )

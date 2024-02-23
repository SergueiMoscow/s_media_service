"""
Методы для работы с моделью File
"""
import uuid

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from common.utils import get_header_user_id
from schemas.catalog import CatalogFileRequest, CatalogFileResponse
from services.catalog import file_add_data_service, get_user_tags_service

router = APIRouter(prefix='/catalog')


@router.post('')
async def add_or_change_data(data: CatalogFileRequest) -> CatalogFileResponse:
    result = await file_add_data_service(data)
    return CatalogFileResponse(result=result)


@router.get('/tags')
async def get_user_tags(user_id: uuid.UUID = Depends(get_header_user_id)):
    result = await get_user_tags_service(user_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content={'result': result})

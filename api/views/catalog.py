"""
Методы для работы с моделью File
"""
from fastapi import APIRouter

from schemas.catalog import CatalogFileRequest, CatalogFileResponse
from services.catalog import file_add_data_service

router = APIRouter(prefix='/catalog')


@router.post('')
async def add_or_change_data(data: CatalogFileRequest) -> CatalogFileResponse:
    result = await file_add_data_service(data)
    return CatalogFileResponse(result=result)

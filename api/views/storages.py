import uuid
from typing import Optional

from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse

from common.exceptions import BadRequest, InvalidKey, NotFound
from common.utils import get_header_user_id
from schemas.storage import (
    CreateStorage,
    CreateStorageResponse,
    StorageListResponse,
    StorageResponse,
    StorageUpdate,
)
from services.storages import (
    create_storage_service,
    delete_storage_service,
    get_list_storages_service,
    get_storage_by_id_service,
    update_storage_service,
)

router = APIRouter(prefix='/storages')


@router.post('/')
async def create_storage(new_storage: CreateStorage) -> CreateStorageResponse:
    try:
        storage = await create_storage_service(new_storage)
        return CreateStorageResponse(new_storage_id=storage.id)
    except InvalidKey:
        raise InvalidKey()
    # except Exception as e:
    #     print(f'Error: {e}')


@router.get('/{storage_id}')
async def get_storage_by_id(storage_id: uuid.UUID) -> StorageResponse:
    try:
        storage = await get_storage_by_id_service(storage_id)
        return StorageResponse.model_validate(storage)
    except BadRequest:
        raise BadRequest(error_code='invalid_request', error_message='Invalid request')
        # print(f'Error: {e}')


@router.patch('/{storage_id}', response_model=StorageResponse)
async def patch_storage(storage_id: uuid.UUID, update_data: StorageUpdate) -> StorageResponse:
    storage = await update_storage_service(storage_id, update_data)
    if not storage:
        raise NotFound(error_message='Storage not found')
    return storage


@router.delete('/{storage_id}')
async def delete_storage(storage_id: uuid.UUID):
    result = await delete_storage_service(storage_id)
    return JSONResponse(content={'deleted': result})


@router.get('/')
async def get_list_storages(user_id: uuid.UUID = Depends(get_header_user_id)):
    results = await get_list_storages_service(user_id=user_id)
    return StorageListResponse(count=len(results), results=results)

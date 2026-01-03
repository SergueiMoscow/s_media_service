import json

from fastapi import APIRouter, Request, Depends, HTTPException
from uuid import UUID
from pathlib import Path
import shutil
from datetime import datetime

from common.utils import get_header_user_id, get_client_ip
from schemas.catalog import CatalogFileRequest
from services.catalog import file_add_data_service
from services.new_file import save_uploaded_file_raw  # новая функция, см. ниже

router = APIRouter()


@router.post("/upload")
async def upload_file(
    request: Request,
    original_filename: str,           # обязательно от Django
    note: str | None = None,
    tags: str | None = None,          # "cat,funny" или JSON-строка
    is_public: bool = False,
    user_id: UUID = Depends(get_header_user_id),
):

    # Читаем сырые байты файла из тела
    file_content = await request.body()
    if not file_content:
        raise HTTPException(status_code=400, detail="Empty file")

    file_info = await save_uploaded_file_raw(
        user_id=user_id,
        file_content=file_content,
        original_filename=original_filename,
    )

    # Парсим теги
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list):
                tags_list = None
        except json.JSONDecodeError:
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Формируем folder_path
    relative_path_full = file_info["relative_path"]
    folder_path = str(Path(relative_path_full).parent)
    if folder_path == ".":
        folder_path = ""

    catalog_request = CatalogFileRequest(
        user_id=user_id,
        ip=get_client_ip(request),
        filename=file_info["filename"],
        storage_id=file_info["storage_id"],
        folder_path=folder_path,
        note=note,
        is_public=is_public,
        tags=tags_list,
    )

    result = await file_add_data_service(data=catalog_request)

    return {
        "status": "success",
        "file": {
            "id": str(result.id),
            "filename": file_info["filename"],
            "original_filename": original_filename,
            "relative_path": relative_path_full,
            "folder_path": folder_path,
            "size": file_info["size"],
            "content_type": file_info.get("content_type", "application/octet-stream"),
            "note": result.note,
            "is_public": result.is_public,
            "tags": result.tags or [],
            "created_at": result.created_at.isoformat() if result.created_at else datetime.now().isoformat(),
        }
    }

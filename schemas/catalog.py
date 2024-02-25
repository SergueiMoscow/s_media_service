import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, field_validator
from starlette import status

from schemas.storage import EmojiCount


class CatalogFileRequest(BaseModel):
    """
    user_id: uuid.UUID
    ip: str
    id: uuid.UUID | None = None
    filename: str | None = None
    storage_id: uuid.UUID | None = None
    folder_path: str | None = None
    # Параметры элемента
    note: str | None = None
    is_public: bool = False
    tag: str | None = None
    emoji: str | None = None
    """

    user_id: uuid.UUID | None = None  # Подставляется позже из header, поэтому None
    ip: str
    # Параметры идентификации
    # Либо id
    id: uuid.UUID | None = None
    # либо storage + folder + filename
    filename: str | None = None
    storage_id: uuid.UUID | None = None
    folder_path: str | None = None
    # Параметры элемента
    note: str | None = None
    is_public: bool | None = None  # None - не меняется.
    tags: List[str] | None = None
    emoji: str | None = None

    @field_validator('folder_path')
    @classmethod
    def strip_folder_path(cls, value: str) -> str:
        return value.lstrip('/')


class CatalogFileResponseResult(BaseModel):
    """
    То, что возвращаем на FrontEnd
    """

    id: uuid.UUID
    is_public: bool | None = None
    note: str | None = None
    tags: list[str] = []
    emoji: list[EmojiCount] = []
    created_at: datetime = None


class CatalogFileResponse(BaseModel):
    status_code: int = status.HTTP_200_OK
    result: CatalogFileResponseResult


class ListCatalogFilesResponse(BaseModel):
    files: List[CatalogFileResponseResult]
    status_code: int = status.HTTP_200_OK


class CreateTagParams(BaseModel):
    """
    Параметры для repositories/create_tag
    """

    file_id: uuid.UUID
    tag_name: str
    user_id: uuid.UUID
    ip: str


# class CreateEmojiParams(BaseModel):
#     """
#     Параметры для repositories/create_or_remove_emoji
#     """
#     session: AsyncSession
#     file_id: uuid.UUID
#     emoji_name: Emoji
#     user_id: uuid.UUID
#     ip: str

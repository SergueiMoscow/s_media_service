import uuid

import sqlalchemy
from pydantic import BaseModel

from db.connector import AsyncSession
from schemas.storage import EmojiCount, Emoji


class CatalogFileRequest(BaseModel):
    """
    user_id: uuid.UUID
    id: uuid.UUID | None = None
    filename: str | None = None
    storage_id: uuid.UUID | None = None
    folder_path: str | None = None
    # Параметры элемента
    note: str | None = None
    tag: str | None = None
    emoji: str | None = None
    """
    user_id: uuid.UUID
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
    tag: str | None = None
    emoji: str | None = None


class CatalogFileResponse(BaseModel):
    """
    То, что возвращаем на FrontEnd
    """
    id: uuid.UUID
    note: str | None = None
    tags: list[str] = []
    emoji: list[EmojiCount] = []


class CreateTagParams(BaseModel):
    """
    Параметры для repositories/create_tag
    """
    file_id: uuid.UUID
    tag_name: str
    user_id: uuid.UUID
    ip: str


class CreateEmojiParams(BaseModel):
    """
    Параметры для repositories/create_or_remove_emoji
    """
    session: AsyncSession
    file_id: uuid.UUID
    emoji_name: Emoji
    user_id: uuid.UUID
    ip: str

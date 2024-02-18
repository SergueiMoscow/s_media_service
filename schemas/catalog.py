import uuid

from pydantic import BaseModel

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
    is_public: bool | None = None  # None - не меняется.
    tag: str | None = None
    emoji: str | None = None


class CatalogFileResponseResult(BaseModel):
    """
    То, что возвращаем на FrontEnd
    """

    id: uuid.UUID
    is_public: bool | None = None
    note: str | None = None
    tags: list[str] = []
    emoji: list[EmojiCount] = []


class CatalogFileResponse(BaseModel):
    status_code: int = 200
    result: CatalogFileResponseResult


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

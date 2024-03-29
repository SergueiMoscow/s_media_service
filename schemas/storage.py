import uuid
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from db.models import StringSize


class CreateStorage(BaseModel):
    key: str
    user_id: UUID
    name: str = Field(..., min_length=1, max_length=StringSize.LENGTH_255)
    path: str
    created_by: UUID


class Pagination(BaseModel):
    page: int = 1
    per_page: int
    items: int


class CreateStorageResponse(BaseModel):
    new_storage_id: UUID


class StorageUpdate(BaseModel):
    user_id: UUID
    name: str
    path: str
    key: str


class StorageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    path: str
    created_at: datetime
    created_by: uuid.UUID


class StorageListResponse(BaseModel):
    count: int
    results: list[StorageResponse]


class FileGroup(Enum):
    VIDEO = ('video', ['mp4', 'avi', 'mkv'])
    IMAGE = ('image', ['tiff', 'jpg', 'png', 'jpeg'])
    DOC = ('doc', ['doc', 'docx', 'txt'])

    def __init__(self, value, extensions):
        self._value_ = value
        self.extensions = extensions

    def match_extension(self, extension):
        return extension in self.extensions

    @classmethod
    def get_group(cls, extension):
        for group in cls:
            if group.match_extension(extension):
                return group
        return None

    def __str__(self):
        return self.value


class Emoji(Enum):
    HEART = 'heart'
    OK = 'ok'
    FIRE = 'fire'


class EmojiCount(BaseModel):
    name: Emoji
    quantity: int


class StorageFile(BaseModel):
    """
    Схема для информации о файле
    """

    name: str
    type: str  # extension
    full_path: str
    size: int
    created: datetime
    updated: datetime
    group: FileGroup | None = None
    # Data from DB
    note: str | None = None
    is_public: bool = False
    tags: list[str] = []
    emoji: list[EmojiCount] = []


class Count(BaseModel):
    direct: int
    total: int


class Folder(BaseModel):
    """
    Схема для папки с файлами
    """

    name: str
    time: datetime | None = None
    size: int
    folders_count: Count = Field(...)
    files_count: Count = Field(...)
    folders: list['Folder'] = []
    files: list[StorageFile] = []


class StorageFolder(Folder):
    """
    Схема для папки с файлами с привязкой к хранилищу
    """

    storage_id: uuid.UUID
    storage_name: str
    created_by: uuid.UUID
    path: str  # Путь внутри хранилища


Folder.model_rebuild()
StorageFolder.model_rebuild()


class StorageSummaryResponse(BaseModel):
    results: list[StorageFolder]


class FolderContentResponse(BaseModel):
    results: StorageFolder
    pagination: Pagination

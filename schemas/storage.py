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


class CreateStorageResponse(BaseModel):
    new_storage_id: UUID


class StorageUpdate(BaseModel):
    user_id: UUID
    name: str
    path: str


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
    IMAGE = ('image', ['tiff', 'jpg', 'png'])
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


class StorageFolder(BaseModel):
    """
    Схема для папки с файлами
    """

    name: str
    time: datetime
    size: int
    folders_count: int
    files_count: int
    folders: list['StorageFolder'] = []
    files: list[StorageFile] = []


StorageFolder.model_rebuild()

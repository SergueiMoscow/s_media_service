import uuid
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from db.models import StringSize


class CreateStorage(BaseModel):
    key: str
    user: UUID
    name: str = Field(..., min_length=1, max_length=StringSize.LENGTH_255)
    path: str
    created_by: UUID


class CreateStorageResponse(BaseModel):
    new_storage_id: UUID


class StorageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    path: str
    created_at: datetime
    created_by: uuid.UUID


class StorageUpdate(BaseModel):
    name: str
    path: str


class StorageListResponse(BaseModel):
    content: list[StorageResponse]

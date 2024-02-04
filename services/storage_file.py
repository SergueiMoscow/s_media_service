import os
import pathlib
import uuid
from io import BytesIO
from os.path import splitext

from PIL import Image
from starlette.responses import FileResponse, StreamingResponse

from db.models import Storage
from schemas.storage import FileGroup
from services.storages import get_storage_by_id_service


class ResponseFile:
    def __init__(self, filename: str, width: int | None = None):
        self.filename = filename
        self.extension = splitext(filename)[1].lstrip(".")
        self.group = FileGroup.get_group(self.extension)
        self.width = width

    async def get_preview(self):
        if self.group == FileGroup.IMAGE:
            return await self.get_resized_image()
        return FileResponse(self.filename, media_type=f"{str(self.group)}/{self.get_media_type()}")

    def get_media_type(self):
        if self.extension == 'jpg':
            return 'jpeg'
        return self.extension.lower()

    async def get_resized_image(self):
        with Image.open(self.filename) as img:
            # Определение, нужно ли изменять размер изображения
            if self.width and img.width > self.width:
                ratio = self.width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.width, new_height), Image.HAMMING)

            byte_io = BytesIO()
            img.save(byte_io, format=self.get_media_type())
            byte_io.seek(0)  # перемещаем курсор в начало файла перед чтением

        return StreamingResponse(byte_io, media_type=f"image/{self.get_media_type()}")


async def get_storage_file_service(storage_id: uuid.UUID, folder: str, filename: str, width: int | None = None):
    storage = await get_storage_by_id_service(storage_id=storage_id)
    if folder.startswith('/'):
        folder = folder[1:]
    full_path = os.path.join(storage.path, folder, filename)
    result = ResponseFile(full_path, width)
    return await result.get_preview()

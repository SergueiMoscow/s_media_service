import os
import uuid
from io import BytesIO
from os.path import splitext

import aiofiles
# import cv2
from PIL import Image
from starlette.responses import FileResponse, StreamingResponse

from schemas.storage import FileGroup
from services.range_requests import range_requests_response
from services.storages import get_storage_by_id_service


class ResponseFile:
    def __init__(self, filename: str, width: int | None = None):
        self.filename = filename
        self.extension = splitext(filename)[1].lstrip('.')
        self.group = FileGroup.get_group(self.extension)
        self.width = width

    async def get_preview(self):
        if self.group == FileGroup.IMAGE:
            return await self.get_resized_image()
        elif self.group == FileGroup.VIDEO:
            return await self.generate_video_preview()
        return FileResponse(self.filename, media_type=f"{str(self.group)}/{self.get_media_type()}")

    async def get_file(self):
        if self.group == FileGroup.IMAGE:
            return await self.get_resized_image()
        elif self.group == FileGroup.VIDEO:
            return await self.get_video_file()
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

    async def generate_video_preview(self):
        pass
    #     video_file = cv2.VideoCapture(self.filename)
    #     if not video_file.isOpened():
    #         raise ValueError(f"Could not open video file {self.filename}")
    #     # Читаем первый кадр видео
    #     ret, frame = video_file.read()
    #     if not ret:
    #         raise ValueError(f"Could not read frame from video file {self.filename}")
    #     is_success, buffer = cv2.imencode(".jpg", frame)
    #     if not is_success:
    #         raise ValueError(f"Could not encode frame to .jpg from video file {self.filename}")
    #     byte_io = BytesIO(buffer.tostring())  # возвращаем "курсор" в начало файла
    #     video_file.release()
    #     cv2.destroyAllWindows()
    #
    #     return StreamingResponse(byte_io, media_type="image/jpeg")

    async def get_video_file(self):
        return range_requests_response(self.filename, content_type="video/mp4")


async def get_storage_file_service(
    storage_id: uuid.UUID, folder: str, filename: str, width: int | None = None, preview: bool = True
):
    storage = await get_storage_by_id_service(storage_id=storage_id)
    folder = folder.lstrip('/')
    full_path = os.path.join(storage.path, folder, filename)
    result = ResponseFile(full_path, width)
    if preview:
        return await result.get_preview()
    else:
        return await result.get_file()

import os
import uuid
from io import BytesIO
from os.path import splitext

import cv2
from PIL import Image, ExifTags
from starlette.responses import FileResponse, StreamingResponse

from schemas.storage import FileGroup
from services.CacheManager import CacheManager
from services.range_requests import range_requests_response
from services.storages import get_storage_by_id_service


class ResponseFile:
    def __init__(
        self,
        filename: str,
        cache_manager: CacheManager | None = None,
        width: int | None = None,
    ):
        if not width:
            raise ValueError("Width must be defined")
        self.filename = filename
        if cache_manager is None:
            self.cache_manager = CacheManager(self.filename)
        self.extension = splitext(filename)[1].lstrip('.')
        self.group = FileGroup.get_group(self.extension)
        self.width = width
        self.cache_manager = cache_manager

    async def get_preview(self) -> FileResponse | StreamingResponse:
        if self.group == FileGroup.IMAGE:
            return await self.get_resized_image()
        if self.group == FileGroup.VIDEO:
            return await self.generate_video_preview()
        return FileResponse(self.filename, media_type=f"{str(self.group)}/{self.get_media_type()}")

    async def get_file(self) -> FileResponse | StreamingResponse:
        if self.group == FileGroup.IMAGE:
            return await self.get_resized_image()
        if self.group == FileGroup.VIDEO:
            return await self.get_video_file()
        return FileResponse(self.filename, media_type=f"{str(self.group)}/{self.get_media_type()}")

    def get_media_type(self) -> str:
        if self.extension == 'jpg':
            return 'jpeg'
        return self.extension.lower()

    async def get_resized_image(self) -> FileResponse | StreamingResponse:
        if self.width and self.cache_manager.is_file_cached(width=self.width):
            cached_file = self.cache_manager.get_cached_file(width=self.width)
            return FileResponse(cached_file, media_type=f'image/{self.get_media_type()}')

        with Image.open(self.filename) as img:
            # Попытка получить тег ориентации и применять его
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break

                exif = img._getexif()
                if exif is not None:
                    orientation = exif.get(orientation)

                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
            except Exception as e:
                # Можем логировать или обрабатывать ошибку иначе, если нужно
                print(f"Error processing EXIF orientation: {e}")

            # Определение, нужно ли изменять размер изображения
            if self.width and img.width > self.width:
                ratio = self.width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.width, new_height), Image.HAMMING)

            self.cache_manager.save_to_cache(img, self.width)

            byte_io = BytesIO()
            img.save(byte_io, format=self.get_media_type())
            byte_io.seek(0)  # перемещаем курсор в начало файла перед чтением

        return StreamingResponse(byte_io, media_type=f"image/{self.get_media_type()}")
    async def generate_video_preview(self) -> FileResponse | StreamingResponse:
        if self.width and self.cache_manager.is_file_cached(width = self.width):
            cached_file = self.cache_manager.get_cached_file(width = self.width)
            return FileResponse(cached_file, media_type='image/jpeg')
        video_file = cv2.VideoCapture(self.filename)
        if not video_file.isOpened():
            raise ValueError(f"Could not open video file {self.filename}")
        # Читаем первый кадр видео
        ret, frame = video_file.read()
        if not ret:
            raise ValueError(f"Could not read frame from video file {self.filename}")
        is_success, buffer = cv2.imencode('.jpg', frame)
        if not is_success:
            raise ValueError(f"Could not encode frame to .jpg from video file {self.filename}")

        self.cache_manager.save_to_cache(Image.fromarray(frame), self.width)

        byte_io = BytesIO(buffer.tobytes())  # возвращаем "курсор" в начало файла
        video_file.release()
        cv2.destroyAllWindows()

        return StreamingResponse(byte_io, media_type='image/jpeg')

    async def get_video_file(self) -> StreamingResponse:
        return range_requests_response(self.filename, content_type='video/mp4')


async def get_storage_file_service(
    storage_id: uuid.UUID,
    folder: str,
    filename: str,
    width: int | None = None,
    preview: bool = True,
) -> StreamingResponse:
    storage = await get_storage_by_id_service(storage_id=storage_id)
    folder = folder.lstrip('/')
    full_path = os.path.join(storage.path, folder, filename)
    cache_manager = CacheManager(full_path)
    result = ResponseFile(filename=full_path, cache_manager=cache_manager, width=width)
    if preview:
        return await result.get_preview()
    return await result.get_file()

import os
from pathlib import Path
from PIL import Image

from common.settings import settings


class CacheManager:
    def __init__(self, original_path: str):
        self.original_path = original_path
        self.cache_dir = str(os.path.join(settings.CACHE_DIR, os.path.dirname(original_path)[1:]))
        os.makedirs(self.cache_dir, mode=0o777, exist_ok=True)

    def _get_cache_file_path(self, width: int) -> str:
        # Формируем путь до файла кэша
        base_name = f'{Path(self.original_path).stem}_{width}.jpg'
        return os.path.join(self.cache_dir, base_name)

    def is_file_cached(self, width: int) -> bool:
        cache_path = self._get_cache_file_path(width)
        return os.path.exists(cache_path)

    def get_cached_file(self, width: int) -> str:
        return self._get_cache_file_path(width)

    def save_to_cache(self, img: Image.Image, width: int) -> None:
        cache_path = self._get_cache_file_path(width)
        file_extension = os.path.splitext(cache_path)[1].lower()  # Получаем расширение файла
        if file_extension in ['.jpg', '.jpeg']:
            # Конвертируем изображение в RGB, если оно содержит альфа-канал
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            img.save(cache_path, format='JPEG')
        elif file_extension == '.png':
            img.save(cache_path, format='PNG')
        else:
            raise ValueError(f'Unsupported file extension: {file_extension}')

    def save_bytes_to_cache(self, byte_string: bytes, width: int):
        with open(self._get_cache_file_path(width=width), 'wb') as f:
            f.write(byte_string)

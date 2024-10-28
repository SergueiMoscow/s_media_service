import os
from pathlib import Path
from PIL import Image

from common.settings import ROOT_DIR, settings
from services.CacheManager import CacheManager

FILE_PATH = os.path.join(ROOT_DIR, 'images/folder.png')
WIDTH = 100

def test_cache_creation(temp_cache_dir):
    cache_manager = CacheManager(FILE_PATH)
    assert os.path.exists(cache_manager.cache_dir)

def test_is_cached(temp_cache_dir):
    settings.CACHE_DIR = temp_cache_dir
    cache_manager = CacheManager(FILE_PATH)
    assert not cache_manager.is_file_cached(width = WIDTH)
    cached_file_path = cache_manager.get_cached_file(width = WIDTH)
    with open(cached_file_path, 'w') as f:
        f.write('test')
    assert cache_manager.is_file_cached(width = WIDTH)


def test_save_to_cache(temp_cache_dir):
    file_path = "test_image.jpg"
    full_path = Path(file_path)
    width = 200
    cache_manager = CacheManager(full_path)

    # Создаем простое изображение
    img = Image.new('RGB', (width, width))

    # Сохраняем изображение в кэш
    cache_manager.save_to_cache(img, file_path, width)

    cached_file_path = cache_manager.get_cached_file(width = width)

    # Проверяем, что изображение сохранилось в кэш
    assert os.path.exists(cached_file_path)

    # Проверяем, что кэшированный файл действительно является изображением
    with Image.open(cached_file_path) as cached_img:
        assert cached_img.size == (width, width)
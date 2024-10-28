import os
import random
import uuid

from PIL import Image

from common.settings import CACHE_COLLAGE_FILE
from db.connector import AsyncSession
from repositories.storages import get_list_storages
from schemas.storage import StorageFolder
from services.CacheManager import CacheManager
from services.collage_maker import CollageMaker
from services.storage_manager import StorageManager
from services.storages import get_storage_by_id_service

COLLAGE_HEIGHT = 400
COLLAGE_WIDTH = 300


async def get_storages_summary_service(user_id: uuid.UUID) -> list[StorageFolder]:
    async with AsyncSession() as session:
        storages = await get_list_storages(session=session, user_id=user_id)
    results = []
    for storage in storages:
        storage_manager = StorageManager(storage)
        results.append(await storage_manager.get_storage_summary())
    return results


def get_random_image_files_from_folder(folder, count) -> list:
    extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
    files = [file for file in os.listdir(folder) if file.lower().endswith(extensions)]
    if len(files) > count:
        return random.sample(files, count)
    return files


async def get_storage_collage_service(
    storage_id: uuid.UUID,
    folder: str,
    force: bool = False,
):
    storage = await get_storage_by_id_service(storage_id=storage_id)
    folder = folder.lstrip('/')
    if storage is None:
        raise ValueError(f'Storage does not exist: {storage_id}')
    full_path_folder = os.path.join(storage.path, folder)
    if not os.path.exists(full_path_folder):
        return CollageMaker.generate_image_with_text('Wrong folder')
    # Проверка есть ли картинка в кэше
    cache_manager = CacheManager(os.path.join(full_path_folder, CACHE_COLLAGE_FILE))
    if cache_manager.is_file_cached(width=COLLAGE_WIDTH) and not force:
        with open(cache_manager.get_cached_file(width=COLLAGE_WIDTH), 'rb') as img:
            return img.read()
    image_files = get_random_image_files_from_folder(folder=full_path_folder, count=10)
    full_path_image_files = [os.path.join(full_path_folder, filename) for filename in image_files]
    collage_maker = CollageMaker(
        height=COLLAGE_HEIGHT, width=COLLAGE_WIDTH, image_files=full_path_image_files
    )
    if len(image_files) == 0:
        return CollageMaker.generate_image_with_text(
            'No files', width=COLLAGE_WIDTH, height=COLLAGE_HEIGHT
        )
    generated_collage_image = collage_maker.generate_image()
    cache_manager.save_bytes_to_cache(generated_collage_image, COLLAGE_WIDTH)
    return generated_collage_image


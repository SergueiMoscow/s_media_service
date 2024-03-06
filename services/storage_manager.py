import os
from datetime import datetime
from enum import Enum
from itertools import islice
from pathlib import Path
from typing import List, Tuple

from db.models import Storage
from schemas.storage import Count, FileGroup, Folder, StorageFile, StorageFolder
from services.catalog import get_file_data_from_catalog_by_fullname, get_files_by_names_service, \
    get_files_data_from_catalog_by_names_list

PAGE_SIZE = 20


class OrderFolder(Enum):
    NAME = 'name'
    TIME = 'time'
    SIZE = 'size'
    FILES_COUNT = 'files_count'
    FOLDERS_COUNT = 'folders_count'


class FolderManager:
    max_files = 100
    max_folders = 100

    def __init__(
        self, storage_path: str,
        order_by: OrderFolder = OrderFolder.NAME,
        page_number: int = 1,
        page_size: int = PAGE_SIZE
    ):
        self.path = storage_path
        self.order_by = order_by
        self.page_number = page_number
        self.page_size = page_size

    @staticmethod
    def _get_size(path) -> int:
        total = 0
        for dir_path, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dir_path, f)
                total += os.path.getsize(fp) if os.path.isfile(fp) else 0
        return total

    @staticmethod
    def _get_counts(path) -> ((int, int), (int, int)):
        folder_count = file_count = 0
        direct_folder_count = direct_file_count = -1  # Случай, когда основная директория считается

        for _, dir_names, file_names in os.walk(path):
            folder_count += len(dir_names)
            file_count += len(file_names)

            if direct_folder_count == -1:  # Если это первая итерация цикла
                direct_folder_count += len(dir_names) + 1  # то считаем количество папок и файлов
                direct_file_count += len(file_names) + 1  # внутри текущей папки

        # return (direct_folder_count, folder_count), (direct_file_count, file_count)
        return {'direct': direct_folder_count, 'total': folder_count}, {
            'direct': direct_file_count,
            'total': file_count,
        }

    async def get_folder_summary(self, trim_start_name: str = '') -> Folder:
        folders_count, files_count, size = await self._count_elements_and_size(self.path)
        try:
            time_last_modified = os.path.getmtime(self.path)
        except Exception:  # pylint: disable=broad-exception-caught
            time_last_modified = None
        if self.path.startswith(trim_start_name):
            trimmed_path = self.path[len(trim_start_name) :]
        else:
            trimmed_path = self.path
        time_last_modified = (
            None if time_last_modified is None else datetime.fromtimestamp(time_last_modified)
        )
        return Folder(
            name=trimmed_path,
            time=time_last_modified,
            size=size,
            folders_count=Count(**folders_count),
            files_count=Count(**files_count),
        )

    async def get_folder_content(self, order_by: OrderFolder = OrderFolder.NAME) -> Folder:
        start_index = (self.page_number - 1) * self.page_size
        end_index = start_index + self.page_size

        nested_folders, nested_files = await self._fetch_separated_folder_and_files()
        # Здесь имеем отдельно несортированные папки и файлы.

        # Сортируем:
        if order_by:
            self.order_by = order_by
        nested_folders = sorted(nested_folders, key=lambda x: getattr(x, self.order_by.value))
        nested_files = sorted(nested_files, key=lambda x: getattr(x, self.order_by.value))

        # Получаем срез пагинации
        pagination = self._paginate(len(nested_folders), len(nested_files))
        nested_folders = nested_folders[pagination[0]:pagination[1]]
        nested_files = nested_files[pagination[2]:pagination[3]]

        # Дополняем nested_files данными из БД:
        nested_files = await get_files_data_from_catalog_by_names_list(nested_files)

        time_last_modified = os.path.getmtime(self.path)
        folders_count, files_count, size = await self._count_elements_and_size(self.path)

        return Folder(
            name=self.path,
            time=datetime.fromtimestamp(time_last_modified),
            size=size,
            folders_count=Count(**folders_count),
            files_count=Count(**files_count),
            folders=nested_folders,
            files=nested_files,
        )

    async def _fetch_separated_folder_and_files(self) -> Tuple[List[Folder], List[StorageFile]]:
        nested_folders = []
        nested_files = []

        for name in os.listdir(self.path):
            nested_full_path = os.path.join(self.path, name)
            time_last_modified = os.path.getmtime(nested_full_path)
            nested_folders_count, nested_files_count, size = await self._count_elements_and_size(
                nested_full_path
            )

            if os.path.isdir(nested_full_path):
                obj = Folder(
                    name=name,
                    time=datetime.fromtimestamp(time_last_modified),
                    size=size,
                    folders_count=Count(**nested_folders_count),
                    files_count=Count(**nested_files_count),
                )
                nested_folders.append(obj)

            elif os.path.isfile(nested_full_path):
                file_info = await self.get_file_info(nested_full_path)
                # catalog_info = await get_file_data_from_catalog_by_fullname(nested_full_path)
                # Инфу из БД сюда не ставим, т.к. она нужно ТОЛЬКО на срез пагинации.
                nested_files.append(StorageFile(**file_info))
        return nested_folders, nested_files

    def _paginate(self, folders_count, files_count):
        start_index = (self.page_number - 1) * self.page_size
        end_index = start_index + self.page_size

        if start_index < folders_count:
            folder_start = start_index
            folder_end = min(end_index, folders_count)
            file_start = 0
            file_end = max(0, end_index - folders_count)
        else:
            folder_start = folders_count
            folder_end = folders_count
            file_start = start_index - folders_count
            file_end = min(end_index - folders_count, files_count)

        return folder_start, folder_end, file_start, file_end

    async def _count_elements_and_size(self, full_path) -> tuple:
        """
        Вызывает методы подсчёта папок, файлов и размера папки
        """
        folders_count, files_count = self._get_counts(full_path)
        size = self._get_size(full_path)
        return folders_count, files_count, size

    async def get_file_info(self, full_path: str) -> dict:
        # try:
        type_ = os.path.splitext(full_path)[1][1:]  # get file extension
        created = datetime.fromtimestamp(os.path.getctime(full_path))
        updated = datetime.fromtimestamp(os.path.getmtime(full_path))
        size = os.path.getsize(full_path)
        group = FileGroup.get_group(type_)

        return {
            'name': os.path.basename(full_path),
            'type': type_,
            'full_path': full_path,
            'size': size,
            'created': created,
            'updated': updated,
            'group': group,
        }
        # except Exception as ex:
        #     # Just print the exception and return an empty dict
        #     print('Failed to get file info for: {}. Exception: {}'.format(full_path, ex))
        #     return {}

    async def create_collage(self):
        pass


class StorageManager:
    def __init__(
        self,
        storage: Storage,
        storage_path: str = '',  # Путь внутри хранилища, без / в начале
        order_by: OrderFolder = OrderFolder.NAME,
        page_number: int = 1,
        page_size: int = PAGE_SIZE,
    ):
        self.storage = storage
        self.page_number = page_number
        self.order_by = order_by
        self.page_size = page_size
        self.storage_path = storage_path.lstrip('/')  # Путь внутри хранилища, без / в начале

        self.folder = FolderManager(
            storage_path=os.path.join(storage.path, self.storage_path),
            order_by=self.order_by,
            page_number=page_number,
            page_size=page_size,
        )

    async def get_storage_folder_content(
        self,
    ) -> StorageFolder:
        folder = await self.folder.get_folder_content()
        # Убираем путь хранилища из folder.name
        folder.name = self.storage_path
        # Убираем путь хранилища из файлов (folder.files)
        for file in folder.files:
            file.full_path = file.full_path.replace(self.storage.path + '/', '', 1)
        return await self.create_storage_folder_object(folder)

    async def get_storage_summary(self) -> StorageFolder:
        folder = await self.folder.get_folder_summary(trim_start_name=self.storage.path)
        return await self.create_storage_folder_object(folder)

    async def create_storage_folder_object(self, folder: Folder) -> StorageFolder:
        return StorageFolder(
            storage_id=self.storage.id,
            storage_name=self.storage.name,
            path=self.storage_path,
            created_by=self.storage.created_by,
            **folder.model_dump(),
        )

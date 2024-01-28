import os
from datetime import datetime
from enum import Enum
from itertools import islice

from schemas.storage import FileGroup, StorageFile, StorageFolder

PAGE_SIZE = 100


class OrderStorage(Enum):
    NAME = 'name'
    TIME = 'time'
    SIZE = 'size'
    FILES_COUNT = 'files_count'
    FOLDERS_COUNT = 'folders_count'


class StorageManager:
    max_files = 100
    max_folders = 100

    def __init__(self, storage_path: str, page_number: int = 1, page_size: int = PAGE_SIZE):
        self.path = storage_path
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
    def _get_counts(path) -> (int, int):
        folder_count = 0
        file_count = 0
        for _, dir_names, file_names in os.walk(path):
            folder_count += len(dir_names)
            file_count += len(file_names)
        return folder_count, file_count

    async def get_storage_summary(self) -> StorageFolder:
        folders_count, files_count, size = await self._count_elements_and_size(self.path)
        time_last_modified = os.path.getmtime(self.path)
        return StorageFolder(
            name=self.path,
            time=datetime.fromtimestamp(time_last_modified),
            size=size,
            folders_count=folders_count,
            files_count=files_count,
        )

    async def get_storage_content(
        self, order_by: OrderStorage = OrderStorage.NAME
    ) -> StorageFolder:
        start = (self.page_number - 1) * self.page_size
        end = start + self.page_size

        nested_folders = []
        nested_files = []

        for name in os.listdir(self.path):
            nested_full_path = os.path.join(self.path, name)
            time_last_modified = os.path.getmtime(nested_full_path)
            nested_folders_count, nested_files_count, size = await self._count_elements_and_size(
                nested_full_path
            )

            if os.path.isdir(nested_full_path):
                obj = StorageFolder(
                    name=name,
                    time=datetime.fromtimestamp(time_last_modified),
                    size=size,
                    folders_count=nested_folders_count,
                    files_count=nested_files_count,
                )
                nested_folders.append(obj)

            elif os.path.isfile(nested_full_path):
                nested_files.append(StorageFile(**self.get_file_info(nested_full_path)))

        nested_folders = sorted(nested_folders, key=lambda x: getattr(x, order_by.value))
        nested_files = sorted(nested_files, key=lambda x: getattr(x, order_by.value))

        time_last_modified = os.path.getmtime(self.path)
        folders_count, files_count, size = await self._count_elements_and_size(self.path)

        return StorageFolder(
            name=self.path,
            time=datetime.fromtimestamp(time_last_modified),
            size=size,
            folders_count=folders_count,
            files_count=files_count,
            folders=list(islice(nested_folders, start, end)),
            files=list(islice(nested_files, start, end)),
        )

    async def _count_elements_and_size(self, full_path) -> tuple:
        """
        Вызывает методы подсчёта папок, файлов и размера папки
        """
        folders_count, files_count = self._get_counts(full_path)
        size = self._get_size(full_path)
        return folders_count, files_count, size

    # async def get_files_in_dir(self, path: str) -> List[StorageFile]:
    #     result = []
    #
    #     for filename in os.listdir(path):
    #         full_path = os.path.join(path, filename)
    #
    #         if not os.path.isfile(full_path):
    #             continue
    #
    #         type_ = os.path.splitext(filename)[1][1:]  # get file extension
    #         created = datetime.fromtimestamp(os.path.getctime(full_path))
    #         updated = datetime.fromtimestamp(os.path.getmtime(full_path))
    #         size = os.path.getsize(full_path)
    #
    #         group = FileGroup.get_group(type_)
    #
    #         storage_file = StorageFile(
    #             name=filename,
    #             type=type_,
    #             full_path=full_path,
    #             size=size,
    #             created=created,
    #             updated=updated,
    #             group=group,
    #         )
    #         result.append(storage_file)
    #
    #     return result

    def get_file_info(self, full_path: str) -> dict:
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

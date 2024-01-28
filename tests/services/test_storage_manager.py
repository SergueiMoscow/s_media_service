import os
import uuid
from unittest import mock

from services.storage_content import get_storages_summary_service
from services.storage_manager import OrderStorage, StorageManager


async def test_folder_count_and_size(created_temp_storage_folder):
    storage = StorageManager(created_temp_storage_folder.root_dir)
    content = await storage.get_storage_content(OrderStorage.SIZE)
    assert content.folders_count == created_temp_storage_folder.folders_count
    assert content.files_count == created_temp_storage_folder.files_count
    assert content.size == created_temp_storage_folder.size


async def test_get_storages_summary(storage):
    with mock.patch('services.storage_content.get_list_storages') as storages:
        storage.path = os.path.join(os.path.expanduser('~'), 'Downloads')
        storages.return_value = [storage]
        result = await get_storages_summary_service(uuid.uuid4())
        assert result is not None
        assert 'Downloads' in result[0].name
        assert result[0].size >= 0
        assert result[0].files_count >= 0
        assert isinstance(result[0].folders, list)
        assert isinstance(result[0].files, list)

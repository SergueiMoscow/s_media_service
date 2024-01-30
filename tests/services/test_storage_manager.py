import os
import uuid
from unittest import mock

from services.storage_content import get_storages_summary_service
from services.storage_manager import FolderManager, OrderFolder


async def test_folder_count_and_size(created_temp_storage_folder):
    folder = FolderManager(created_temp_storage_folder.root_dir)
    content = await folder.get_folder_content(OrderFolder.SIZE)
    assert content.folders_count.total == created_temp_storage_folder.folders_count
    assert content.files_count.total == created_temp_storage_folder.files_count
    assert content.size == created_temp_storage_folder.size


async def test_get_storages_summary(storage):
    with mock.patch('services.storage_content.get_list_storages') as storages:
        user_id = uuid.uuid4()
        storage.user_id = user_id
        storage.path = os.path.join(os.path.expanduser('~'), 'Downloads')
        storages.return_value = [storage]
        result = await get_storages_summary_service(user_id=user_id)
        assert result is not None
        assert result[0].name == '/'
        assert result[0].size >= 0
        assert result[0].files_count.total >= 0
        assert isinstance(result[0].folders, list)
        assert isinstance(result[0].files, list)

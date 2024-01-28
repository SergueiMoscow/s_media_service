from services.storage_manager import OrderStorage, StorageManager


async def test_folder_count_and_size(created_temp_storage_folder):
    storage = StorageManager(created_temp_storage_folder.root_dir)
    content = await storage.get_storage_content(OrderStorage.SIZE)
    assert content.folders_count == created_temp_storage_folder.folders_count
    assert content.files_count == created_temp_storage_folder.files_count
    assert content.size == created_temp_storage_folder.size

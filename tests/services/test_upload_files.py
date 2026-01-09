from datetime import datetime
from unittest.mock import MagicMock

import pytest
from uuid import UUID
from pathlib import Path

from db.models import Storage
from services.new_file import get_full_path_for_new_file


class MockUploadFile:
    """Простой мок для UploadFile, чтобы не тянуть зависимости FastAPI в тесты"""
    def __init__(self, filename: str = "test.jpg"):
        self.filename = filename


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_full_path_for_new_file_creates_unique_path(
    created_storage_with_upload: Storage,
    tmp_path: Path,
):
    user_id = created_storage_with_upload.user_id
    test_media_path = tmp_path / "media" / "images"
    created_storage_with_upload.path = str(test_media_path)

    file = MockUploadFile(filename="test.jpg")

    path1 = await get_full_path_for_new_file(user_id=user_id, file=file)

    # Динамически вычисляем ожидаемую директорию на основе текущей даты
    now = datetime.now()
    expected_dir = test_media_path / now.strftime("%Y") / now.strftime("%m")

    assert path1.parent == expected_dir
    assert path1.name == "test.jpg"

    path1.parent.mkdir(parents=True, exist_ok=True)
    path1.touch()

    path2 = await get_full_path_for_new_file(user_id=user_id, file=file)
    assert path2.parent == expected_dir
    assert path2.name == "test_1.jpg"
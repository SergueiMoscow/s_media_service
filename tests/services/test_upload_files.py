import pytest
from uuid import UUID
from fastapi import UploadFile
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
    tmp_path: Path,  # pytest создаёт уникальную временную папку для каждого теста
    monkeypatch,
):
    # Подменяем путь хранилища на нашу временную директорию
    test_media_path = tmp_path / "media" / "images"
    created_storage_with_upload.path = str(test_media_path)

    user_id: UUID = created_storage_with_upload.user_id
    file = MockUploadFile(filename="test.jpg")

    # Первый вызов — должен вернуть test.jpg
    path1 = await get_full_path_for_new_file(user_id=user_id, file=file)
    expected1 = test_media_path / "2026" / "01" / "test.jpg"
    assert path1 == expected1
    assert path1.name == "test.jpg"

    # Создаём файл вручную, чтобы симулировать коллизию
    path1.parent.mkdir(parents=True, exist_ok=True)
    path1.touch()

    # Второй вызов — должен вернуть test_1.jpg
    path2 = await get_full_path_for_new_file(user_id=user_id, file=file)
    expected2 = test_media_path / "2026" / "01" / "test_1.jpg"
    assert path2 == expected2
    assert path2.name == "test_1.jpg"

    # Создаём и этот файл
    path2.touch()

    # Третий вызов — test_2.jpg
    path3 = await get_full_path_for_new_file(user_id=user_id, file=file)
    assert path3.name == "test_2.jpg"
    assert path3.parent == test_media_path / "2026" / "01"

    # Дополнительно: проверяем, что директории создались
    assert path3.parent.exists()

    # tmp_path автоматически удалится после теста — всё чисто!
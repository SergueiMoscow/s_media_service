import pytest
from uuid import uuid4
from pathlib import Path
from datetime import datetime
import json
from unittest.mock import patch, MagicMock

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from api.app import app
from db.connector import AsyncSession
from db.models import Storage, File
from repositories.catalog import get_file_by_name
from services.new_file import save_uploaded_file
from common.utils import get_header_user_id  # для мока

# Глобальный TestClient
client = TestClient(app)


class MockUploadFile:
    """Мок для UploadFile с реальным содержимым"""

    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.content_type = "image/jpeg"
        self.file = MagicMock()
        self.file.read = MagicMock(return_value=content)
        self.file.seek = MagicMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def close(self):
        pass


@pytest.fixture
def user_id() -> uuid4:
    return uuid4()


@pytest.fixture
def test_image_content() -> bytes:
    """Тестовое содержимое файла (1KB)"""
    return b"fake_image_data_" + b"A" * 1024


@pytest.fixture
def test_file_content():
    """Тестовые байты файла (около 1 КБ)"""
    return b"fake_file_content_" + b"A" * 1000


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
@patch('common.utils.get_header_user_id')
async def test_upload_file_successful(
    mock_get_user_id,
    created_storage_with_upload: Storage,
    test_image_content: bytes,
    monkeypatch,
):
    user_id = created_storage_with_upload.user_id
    mock_get_user_id.return_value = user_id

    # Фиксируем дату
    fixed_date = datetime(2025, 1, 3)
    monkeypatch.setattr('services.new_file.datetime', MagicMock(now=lambda: fixed_date))

    # Запрос: raw body + query params
    response = client.post(
        "/upload",
        params={
            "original_filename": "test.jpg",
            "note": "Test image from pytest",
            "tags": json.dumps(["cat", "funny", "test"]),  # передаём как JSON-строку
            "is_public": "true",
        },
        headers={
            "X-User-ID": str(user_id),
            "Content-Type": "application/octet-stream",
        },
        content=test_image_content,  # сырые байты
    )

    assert response.status_code == 200, response.text
    result = response.json()

    assert result["status"] == "success"
    file_data = result["file"]

    assert file_data["original_filename"] == "test.jpg"
    assert file_data["filename"] == "test.jpg"
    assert file_data["relative_path"] == "2025/01/test.jpg"
    assert file_data["folder_path"] == "2025/01"
    assert file_data["size"] == len(test_image_content)
    assert file_data["note"] == "Test image from pytest"
    assert file_data["is_public"] is True
    assert file_data["tags"] == ["cat", "funny", "test"]
    assert file_data["id"] is not None

    # Файл на диске
    expected_path = Path(created_storage_with_upload.path) / "2025" / "01" / "test.jpg"
    assert expected_path.exists()
    assert expected_path.read_bytes() == test_image_content

    # Запись в File
    async with AsyncSession() as session:
        file_record = await get_file_by_name(session, str(expected_path))
        assert file_record is not None
        assert file_record.note == "Test image from pytest"
        assert file_record.is_public is True


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
@patch('common.utils.get_header_user_id')
async def test_upload_file_name_collision(
    mock_get_user_id,
    created_storage_with_upload: Storage,
    test_file_content: bytes,
    monkeypatch,
):
    user_id = created_storage_with_upload.user_id
    mock_get_user_id.return_value = user_id

    fixed_date = datetime(2025, 1, 3)
    monkeypatch.setattr('services.new_file.datetime', MagicMock(now=lambda: fixed_date))

    # Создаём файл вручную для коллизии
    collision_path = Path(created_storage_with_upload.path) / "2025" / "01" / "test.jpg"
    collision_path.parent.mkdir(parents=True, exist_ok=True)
    collision_path.write_bytes(b"existing_file")

    response = client.post(
        "/upload",
        params={
            "original_filename": "test.jpg",
            "note": "Second file",
        },
        headers={"X-User-ID": str(user_id)},
        content=test_file_content,
    )

    assert response.status_code == 200
    result = response.json()["file"]

    assert result["filename"] == "test_1.jpg"
    assert result["relative_path"] == "2025/01/test_1.jpg"
    assert result["note"] == "Second file"

    new_path = Path(created_storage_with_upload.path) / "2025" / "01" / "test_1.jpg"
    assert new_path.exists()
    assert new_path.read_bytes() == test_file_content


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
@patch('common.utils.get_header_user_id')
async def test_upload_empty_file_body(
    mock_get_user_id,
    created_storage_with_upload: Storage,
):
    mock_get_user_id.return_value = created_storage_with_upload.user_id

    response = client.post(
        "/upload",
        params={"original_filename": "empty.jpg"},
        headers={"X-User-ID": str(created_storage_with_upload.user_id)},
        content=b"",  # пустое тело
    )

    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
@patch('common.utils.get_header_user_id')
async def test_upload_missing_filename(
    mock_get_user_id,
    created_storage_with_upload: Storage,
    test_file_content: bytes,
):
    mock_get_user_id.return_value = created_storage_with_upload.user_id

    response = client.post(
        "/upload",
        params={},  # нет original_filename
        headers={"X-User-ID": str(created_storage_with_upload.user_id)},
        content=test_file_content,
    )

    assert response.status_code == 400
    response_json = response.json()
    assert "original_filename Field required" in response.json()["error"]["error_message"]


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
@patch('common.utils.get_header_user_id')
async def test_upload_without_optional_fields(
    mock_get_user_id,
    created_storage_with_upload: Storage,
    test_file_content: bytes,
    monkeypatch,
):
    user_id = created_storage_with_upload.user_id
    mock_get_user_id.return_value = user_id

    fixed_date = datetime(2025, 1, 3)
    monkeypatch.setattr('services.new_file.datetime', MagicMock(now=lambda: fixed_date))

    response = client.post(
        "/upload",
        params={
            "original_filename": "minimal.jpg",
        },
        headers={"X-User-ID": str(user_id)},
        content=test_file_content,
    )

    assert response.status_code == 200
    file_data = response.json()["file"]

    assert file_data["note"] is None
    assert file_data["is_public"] is False
    assert file_data["tags"] == []
    assert file_data["filename"] == "minimal.jpg"
    assert file_data["relative_path"] == "2025/01/minimal.jpg"


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
@patch('common.utils.get_header_user_id')
async def test_upload_tags_as_comma_string(
    mock_get_user_id,
    created_storage_with_upload: Storage,
    test_file_content: bytes,
    monkeypatch,
):
    user_id = created_storage_with_upload.user_id
    mock_get_user_id.return_value = user_id

    fixed_date = datetime(2025, 1, 3)
    monkeypatch.setattr('services.new_file.datetime', MagicMock(now=lambda: fixed_date))

    response = client.post(
        "/upload",
        params={
            "original_filename": "tags_string.jpg",
            "tags": "dog, walk, park",  # строка, не JSON
        },
        headers={"X-User-ID": str(user_id)},
        content=test_file_content,
    )

    assert response.status_code == 200
    file_data = response.json()["file"]
    assert file_data["tags"] == ["dog", "walk", "park"]

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.app import app
from db.models import Storage


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_update_storage(faker):
    with patch('api.views.storages.update_storage_service') as mock:
        mock.return_value = Storage(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name=faker.word(),
            path=faker.word(),
            created_at='2023-01-01T12:00:00',
            created_by=uuid.uuid4(),
        )
        yield mock

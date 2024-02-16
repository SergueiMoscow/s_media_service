import io
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from PIL import Image
from starlette import status

from common.exceptions import BadRequest
from common.settings import settings
from db.connector import AsyncSession
from db.models import Storage
from repositories.storages import create_storage


@pytest.mark.usefixtures('apply_migrations')
def test_create_storage_view_success(client, faker):
    data = {
        'key': settings.KEY,
        'user_id': str(uuid.uuid4()),
        'name': faker.word(),
        'path': faker.word(),
        'created_by': str(uuid.uuid4()),
    }
    response = client.post('/storages', json=data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['new_storage_id'] is not None


def test_create_storage_view_wrong_key(client, faker):
    data = {
        'key': faker.word(),
        'user_id': str(uuid.uuid4()),
        'name': faker.word(),
        'path': faker.word(),
        'created_by': str(uuid.uuid4()),
    }
    # with pytest.raises(BadRequest):
    response = client.post('/storages', json=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error']['error_code'] == 'invalid_key'


def test_create_storage_view_wrong_user(client, faker):
    data = {
        'key': faker.word(),
        'user_id': faker.word(),
        'name': faker.word(),
        'path': faker.word(),
        'created_by': str(uuid.uuid4()),
    }
    response = client.post('/storages', json=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error']['error_code'] == 'incorrect_data'


@pytest.mark.usefixtures('apply_migrations')
def test_get_storage_by_id(client, created_storage):
    url = f'storages/{created_storage.id}'
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_patch_storage_success(client, mock_update_storage):
    storage_id = mock_update_storage.return_value.id
    update_data = {
        'user_id': str(mock_update_storage.return_value.user_id),
        'name': 'Updated name',
        'path': '/updated/path',
    }

    response = client.patch(f"/storages/{storage_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK


def test_patch_storage_not_found(client, mock_update_storage):
    storage_id = uuid.uuid4()
    update_data = {
        'user_id': str(uuid.uuid4()),
        'name': 'Updated name',
        'path': '/updated/path',
    }
    mock_update_storage.return_value = None

    response = client.patch(f"/storages/{storage_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'not found' in response.text.lower()


@pytest.mark.usefixtures('apply_migrations')
def test_patch_storage_wrong_user(client, created_storage):
    storage_id = created_storage.id
    update_data = {
        'user_id': str(uuid.uuid4()),
        'name': 'Updated name',
        'path': '/updated/path',
    }

    response = client.patch(f"/storages/{storage_id}", json=update_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['error']['error_code'] == 'not_allowed'
    assert 'not allowed for user' in response.text.lower()


@pytest.mark.usefixtures('apply_migrations')
def test_delete_storage(client, created_storage):
    response = client.delete(f'/storages/{created_storage.id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['deleted'] == 1


@pytest.mark.usefixtures('apply_migrations', 'created_storage')
def test_get_list_storages_ok(client):
    response = client.get('/storages/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['results'][0]['created_by'] is not None


@pytest.mark.usefixtures('apply_migrations', 'created_storage')
async def test_get_list_storages_with_wrong_storage_path(client, faker):
    async with AsyncSession() as session:
        new_storage = Storage(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name=faker.word(),
            path='wrong_storage_path',
            created_at=datetime.now(),
            created_by=uuid.uuid4(),
        )
        await create_storage(session=session, new_storage=new_storage)
        await session.commit()
    response = client.get('/storages/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == 2


@pytest.mark.usefixtures('apply_migrations')
def test_get_list_storages_by_user(client, created_storage):
    response = client.get(f'/storages/?user_id={created_storage.user_id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['results'][0]['user_id'] == str(created_storage.user_id)


@pytest.mark.usefixtures('apply_migrations', 'created_storage')
def test_get_list_storages_by_wrong_user(client):
    response = client.get(f'/storages/?user_id={uuid.uuid4()}')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == 0


async def test_get_storage_collage_ok(client, storage):
    with patch('services.storages.get_storage_by_id') as mock:
        mock.return_value = storage
        response = client.get(
            f'/storage/collage/{storage.id}', params={'user_id': storage.user_id, 'folder': ''}
        )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert len(response.content) > 0  # проверяем, что данные изображения действительно возвращаются

    # дополнительная проверка на валидность PNG может быть выполнена с помощью библиотеки Pillow
    try:
        Image.open(
            io.BytesIO(response.content)
        ).verify()  # Pillow пытается верифицировать изображение
    except (IOError, SyntaxError) as e:
        pytest.fail(f"Invalid PNG image: {e}")


async def test_get_storage_collage_wrong_path(client, storage):
    with patch('services.storages.get_storage_by_id') as mock:
        storage.path = 'wrong_storage_path'
        mock.return_value = storage
        response = client.get(
            f'/storage/collage/{storage.id}', params={'user_id': storage.user_id, 'folder': ''}
        )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert len(response.content) > 0  # проверяем, что данные изображения действительно возвращаются

    # дополнительная проверка на валидность PNG может быть выполнена с помощью библиотеки Pillow
    try:
        Image.open(
            io.BytesIO(response.content)
        ).verify()  # Pillow пытается верифицировать изображение
    except (IOError, SyntaxError) as e:
        pytest.fail(f"Invalid PNG image: {e}")

import uuid

import pytest
from starlette import status

from common.settings import settings


@pytest.mark.usefixtures('apply_migrations')
def test_create_storage_view_success(client, faker):
    data = {
        'key': settings.KEY,
        'user': str(uuid.uuid4()),
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
        'user': str(uuid.uuid4()),
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
        'user': faker.word(),
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
        'name': 'Updated name',
        'path': '/updated/path',
    }

    response = client.patch(f"/storages/{storage_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK


def test_patch_storage_not_found(client, mock_update_storage):
    storage_id = uuid.uuid4()
    update_data = {
        'name': 'Updated name',
        'path': '/updated/path',
    }
    mock_update_storage.return_value = None

    response = client.patch(f"/storages/{storage_id}", json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'not found' in response.text.lower()


@pytest.mark.usefixtures('apply_migrations')
def test_delete_storage(client, created_storage):
    response = client.delete(f'/storages/{created_storage.id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['deleted'] == 1


@pytest.mark.usefixtures('apply_migrations', 'created_storage')
def test_get_list_storages(client):
    response = client.get('/storages/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['results'][0]['created_by'] is not None


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

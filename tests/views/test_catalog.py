import pytest

from schemas.catalog import CatalogFileRequest
from schemas.storage import Emoji


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'key, value, func',
    (
        ('note', 'test note', lambda result, key, value: result[key] == value),
        ('is_public', True, lambda result, key, value: result[key] == value),
        ('tags', ['test tag'], lambda result, key, value: value[0] in result['tags']),
        (
            'emoji',
            Emoji.OK.value,
            lambda result, key, value: {'name': value, 'quantity': 1} in result[key],
        ),
    ),
)
@pytest.mark.usefixtures('apply_migrations')
async def test_add_or_change_data_by_file_name(client, created_storage, key, value, func):
    extra_param = {key: value}
    data = CatalogFileRequest(
        user_id=str(created_storage.user_id),
        ip='127.0.0.1',
        filename='folder.png',
        storage_id=created_storage.id,
        folder_path='',
        **extra_param,
    )

    json = data.model_dump(mode='json')
    response = client.post('/catalog', json=json)
    response_result = response.json()['result']
    assert func(response_result, key, value)


@pytest.mark.usefixtures('apply_migrations')
def test_user_tags(client, create_file_with_tags_and_emoji):
    number_of_requests = 3
    created_objects = [create_file_with_tags_and_emoji() for _ in range(number_of_requests)]
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    for obj in range(number_of_requests):
        headers['X-USER-ID'] = str(created_objects[obj]['tags'][0].created_by)
        response = client.get('/catalog/tags', headers=headers)
        assert response.json()['results'][0] == created_objects[obj]['tags'][0].name

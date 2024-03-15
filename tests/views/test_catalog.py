from unittest.mock import patch

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
            'tags',
            ['test tag1', 'test tag2'],
            lambda result, key, value: value[0] in result['tags'] and value[1] in result['tags'],
        ),
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


@pytest.mark.usefixtures('apply_migrations')
def test_get_main_page(client, create_file_with_tags_and_emoji, faker):
    number_of_files = faker.random_int(min=4, max=20)
    for counter in range(number_of_files):
        create_file_with_tags_and_emoji(is_public=counter % 2)
    response = client.get('/catalog/main')
    assert response.status_code == 200
    result = response.json()
    assert result is not None

    assert len(result['files']) == number_of_files // 2


@pytest.mark.usefixtures('apply_migrations')
def test_add_multiple_tags_and_delete_tag(client, created_storage, faker):
    data = CatalogFileRequest(
        user_id=str(created_storage.user_id),
        ip='127.0.0.1',
        filename='folder.png',
        storage_id=created_storage.id,
        folder_path='',
        tags=[f'test_{counter}' for counter in range(faker.random_int(min=2, max=10))],
    )

    json = data.model_dump(mode='json')
    response = client.post('/catalog', json=json)
    response_result = response.json()['result']
    for _, tag_name in enumerate(data.tags):
        assert tag_name in response_result['tags']

    tag_to_remove = data.tags[faker.random_int(min=0, max=len(data.tags) - 1)]
    data.tags = []
    data.remove_tag = tag_to_remove
    response = client.post('/catalog', json=json)
    response_result = response.json()['result']
    assert tag_to_remove not in response_result['tags']


@pytest.mark.parametrize(
    'public, is_public',
    (
        ('true', [True]),
        ('false', [False]),
        ('', [True, False]),
    )
)
@pytest.mark.usefixtures('apply_migrations')
def test_catalog_content(client, faker, storage, create_file_with_tags_and_emoji, public, is_public):
    #  http://127.0.0.1:8081/catalog/content?storage_id=960e70e6-98c7-42e1-9b51-723723650042&page=1&per_page=10&public=false
    number_of_records = faker.random_int(min=10, max=20)
    created_objects = [create_file_with_tags_and_emoji() for _ in range(number_of_records)]
    url = f'/catalog/content?storage_id={storage.id}&page=1&per_page=5&public={public}'
    with patch('repositories.catalog.get_storage_by_id') as mock:
        mock.return_value = storage
        response = client.get(url)
    response_result = response.json()
    assert len(response_result['files']) > 0
    for file in response_result['files']:
        assert file['is_public'] in is_public

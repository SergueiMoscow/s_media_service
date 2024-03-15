import os
import random
import uuid
from unittest.mock import patch

import pytest

from common.settings import settings
from schemas.catalog import CatalogFileRequest, CatalogContentRequest
from services.catalog import file_add_data_service, get_file_data_from_catalog_by_fullname, ListCatalogFileResponse, \
    get_catalog_file_service


@pytest.mark.usefixtures('apply_migrations')
async def test_catalog_add_data_service(created_storage):
    full_file_name = 'folder.png'
    new_file = CatalogFileRequest(
        user_id=uuid.uuid4(),
        ip='127.0.0.1',
        filename=full_file_name,
        storage_id=created_storage.id,
        folder_path='',
        note='test',
    )
    result = await file_add_data_service(new_file)
    assert result is not None
    assert result.id is not None
    assert result.note == 'test'


@pytest.mark.usefixtures('apply_migrations')
@pytest.mark.parametrize(
    'attribute_name, attribute_value, assert_function',
    [
        ('note', 'test', lambda result, _: result.note == 'test'),
        ('tags', ['test'], lambda result, _: 'test' in result.tags),
        (
            'emoji',
            'ok',
            lambda result, value: any(
                e.name.value == value and e.quantity == 1 for e in result.emoji
            ),
        ),
    ],
)
async def test_catalog_add_data_service_ok(
    created_storage, attribute_name, attribute_value, assert_function
):
    full_file_name = 'folder.png'
    new_file_data = {
        'user_id': uuid.uuid4(),
        'ip': '127.0.0.1',
        'filename': full_file_name,
        'storage_id': created_storage.id,
        'folder_path': '',
        attribute_name: attribute_value,
    }
    new_file = CatalogFileRequest(**new_file_data)
    result = await file_add_data_service(new_file)

    assert result is not None
    assert result.id is not None
    assert assert_function(result, attribute_value)


@pytest.mark.usefixtures('apply_migrations')
async def test_get_file_data_from_catalog_by_fullname(
    created_storage,
    created_file_with_tags_and_emoji
):
    full_path_file_name = str(
        os.path.join(created_storage.path, created_file_with_tags_and_emoji['file'].name)
    )
    result = await get_file_data_from_catalog_by_fullname(full_path_file_name)
    assert result is not None
    assert created_file_with_tags_and_emoji['file'].note == result['note']
    assert created_file_with_tags_and_emoji['file'].is_public == result['is_public']
    tag_names = [tag.name for tag in created_file_with_tags_and_emoji['tags']]
    assert set(tag_names).issubset(set(result['tags']))


@pytest.mark.usefixtures('apply_migrations')
async def test_list_catalog_file_response(faker, storage, create_file_with_tags_and_emoji):
    number_of_records = faker.random_int(min=10, max=20)
    created_objects = [create_file_with_tags_and_emoji() for _ in range(number_of_records)]
    request = CatalogContentRequest()
    with patch('repositories.catalog.get_storage_by_id') as mock:
        mock.return_value = storage
        files, pagination = await ListCatalogFileResponse().get_files(storage_id=storage.id, params=request)
    assert len(files) <= settings.PER_PAGE
    assert pagination.items == len(created_objects)


@pytest.mark.usefixtures('apply_migrations')
async def test_get_catalog_file_service(faker, storage, create_file_with_tags_and_emoji):
    number_of_records = faker.random_int(min=10, max=20)
    created_objects = [create_file_with_tags_and_emoji() for _ in range(number_of_records)]
    search_file_id = random.choice(created_objects)['file'].id
    result = get_catalog_file_service(file_id=search_file_id)
    assert result is not None

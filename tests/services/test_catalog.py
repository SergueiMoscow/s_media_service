import uuid

import pytest
import os

from schemas.catalog import CatalogFileRequest
from services.catalog import catalog_add_data_service


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
    result = await catalog_add_data_service(new_file)
    assert result is not None
    assert result.id is not None
    assert result.note == 'test'


@pytest.mark.usefixtures('apply_migrations')
@pytest.mark.parametrize(
    "attribute_name, attribute_value, assert_function",
    [
        ('note', 'test', lambda result, _: result.note == 'test'),
        ("tag", "test", lambda result, _: 'test' in result.tags),
        ("emoji", "ok", lambda result, value: any(e.name.value == value and e.quantity == 1 for e in result.emoji))
    ]
)
async def test_catalog_add_data_service_ok(created_storage, attribute_name, attribute_value, assert_function):
    full_file_name = 'folder.png'
    new_file_data = {
        'user_id': uuid.uuid4(),
        'ip': '127.0.0.1',
        'filename': full_file_name,
        'storage_id': created_storage.id,
        'folder_path': '',
        attribute_name: attribute_value
    }
    new_file = CatalogFileRequest(**new_file_data)
    result = await catalog_add_data_service(new_file)

    assert result is not None
    assert result.id is not None
    assert assert_function(result, attribute_value)
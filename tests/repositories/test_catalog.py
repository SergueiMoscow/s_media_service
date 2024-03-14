import random
import re
from unittest.mock import patch

import pytest

from common.settings import settings
from db.connector import AsyncSession
from db.models import File
from repositories.catalog import create_file, get_file_by_name, get_files_by_filter
from schemas.catalog import CatalogContentRequest


@pytest.mark.usefixtures('apply_migrations')
async def test_get_file_by_name_no_exists():
    async with AsyncSession() as session:
        result = await get_file_by_name(session=session, filename='/file_does_not_exist')
        assert result is None


@pytest.mark.usefixtures('apply_migrations')
async def test_create_file_catalog(created_temp_file):
    async with AsyncSession() as session:
        file = await create_file(session, created_temp_file['name'])
        await session.commit()
    assert created_temp_file['size'] == file.size
    assert file.id is not None


@pytest.mark.usefixtures('apply_migrations')
async def test_get_catalog_files(storage, create_file_with_tags_and_emoji, faker):
    number_of_records = faker.random_int(min=10, max=20)
    [
        create_file_with_tags_and_emoji()
        for _ in range(number_of_records)
    ]   # pylint: disable=expression-not-assigned
    request = CatalogContentRequest()
    with patch('repositories.catalog.get_storage_by_id') as mock:
        mock.return_value = storage
        async with AsyncSession() as session:
            result = await get_files_by_filter(session, storage.id, request)
        previous_created_at = None

    assert len(result) == settings.PER_PAGE
    for file in result:
        assert isinstance(file, File)
        if previous_created_at is None:
            previous_created_at = file.created_at
            continue
        previous_created_at = file.created_at
        assert previous_created_at >= file.created_at


@pytest.mark.usefixtures('apply_migrations')
async def test_get_catalog_files_filter_note(storage, create_file_with_tags_and_emoji, faker):
    number_of_records = faker.random_int(min=10, max=20)
    created_objects = [create_file_with_tags_and_emoji() for _ in range(number_of_records)]
    # Берём слово, которое будем искать
    test_note = created_objects[faker.random_int(min=0, max=len(created_objects) - 1)]['file'].note
    words = re.findall(r'\b\w{4,}\b', test_note)
    search_word = random.choice(words)
    request = CatalogContentRequest(
        search=search_word,
    )

    with patch('repositories.catalog.get_storage_by_id') as mock:
        mock.return_value = storage
        async with AsyncSession() as session:
            result = await get_files_by_filter(session, storage.id, request)

    assert len(result) <= settings.PER_PAGE
    for file in result:
        assert isinstance(file, File)
        assert search_word in file.note


@pytest.mark.usefixtures('apply_migrations')
async def test_get_catalog_files_filter_tags(storage, create_file_with_tags_and_emoji, faker):
    number_of_records = faker.random_int(min=10, max=20)
    created_objects = [create_file_with_tags_and_emoji() for _ in range(number_of_records)]
    # Берём тег, который будем искать
    search_tag = random.choice(
        created_objects[faker.random_int(min=0, max=len(created_objects) - 1)]['tags']
    ).name
    request = CatalogContentRequest(
        tags=[search_tag],
    )

    with patch('repositories.catalog.get_storage_by_id') as mock:
        mock.return_value = storage
        async with AsyncSession() as session:
            result = await get_files_by_filter(session, storage.id, request)

            assert len(result) <= settings.PER_PAGE
            for file in result:
                assert isinstance(file, File)
                assert search_tag in [tag.name for tag in file.tags]

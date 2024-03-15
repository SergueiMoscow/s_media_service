import os
import random
import tempfile
import uuid
from datetime import datetime

import pytest
from sqlalchemy import text as sa_text

from alembic import command
from alembic.config import Config
from common.settings import ROOT_DIR, settings
from db import models
from db.connector import AsyncSession, Session
from db.models import Storage
from repositories.storages import create_storage
from schemas.storage import Emoji
from tests.random_temp_folder import RandomTempFolder

TEST_IMAGE_FILE_NAME = 'folder.jpg'


@pytest.fixture
def apply_migrations():
    assert 'TEST' in settings.DATABASE_SCHEMA.upper(), 'Попытка использовать не тестовую схему.'

    alembic_cfg = Config(str(ROOT_DIR / 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', str(ROOT_DIR / 'alembic'))
    command.downgrade(alembic_cfg, 'base')
    command.upgrade(alembic_cfg, 'head')

    yield command, alembic_cfg

    command.downgrade(alembic_cfg, 'base')

    with Session() as session:
        session.execute(sa_text(f'DROP SCHEMA IF EXISTS {settings.DATABASE_SCHEMA} CASCADE;'))
        session.commit()


@pytest.fixture
def storage(faker):
    return Storage(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name=faker.word(),
        path=os.path.join(ROOT_DIR, 'images'),
        created_at=datetime.now(),
        created_by=uuid.uuid4(),
    )


@pytest.fixture
@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def created_storage(storage) -> models.Storage:  # pylint: disable=redefined-outer-name
    async with AsyncSession() as session:
        new_storage = await create_storage(session=session, new_storage=storage)
        await session.commit()
        return new_storage


@pytest.fixture
def created_temp_storage_folder():
    temp_folder = RandomTempFolder()
    try:
        yield temp_folder
    finally:
        temp_folder.destroy()


@pytest.fixture
def created_temp_file():
    with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
        temp_file.write(str(uuid.uuid4()).encode())
        file_name = temp_file.name
        file_info = os.stat(file_name)
        file_size = file_info.st_size  # Размер файла в байтах
        info = {
            'name': file_name,
            'size': file_size,
        }
        yield info


@pytest.fixture
@pytest.mark.usefixtures('apply_migrations')
def create_file_with_tags_and_emoji(storage, faker):  # pylint: disable='redefined-outer-name'
    def _create(
        name: str = os.path.join(storage.path, TEST_IMAGE_FILE_NAME),
        note: str = None,
        is_public: bool = None,
        tags: list | None = None,
        emoji: dict | None = None,
    ):
        if note is None:
            note = faker.sentence(nb_words=20, variable_nb_words=True)
        if is_public is None:
            is_public = random.choice([True, False])
        file = models.File(
            size=faker.random_int(),
            name=name,
            type='jpg',
            note=note,
            is_public=is_public,
            created=faker.date_time_this_decade(),
        )
        with Session() as session:
            session.add(file)
            session.commit()
        if tags is None:
            tags = [
                models.Tag(
                    file_id=file.id,
                    name=faker.word(),
                    ip=faker.bothify(text='###.##.##.##'),
                    created_by=uuid.uuid4(),
                )
                for _ in range(faker.random_int(1, 5))
            ]
        if emoji is None:
            emojis = list(Emoji)
            num_emojis = faker.random_int(min=1, max=len(emojis) - 1)
            emoji = [
                models.Emoji(
                    file_id=file.id,
                    name=random.choice(emojis).value,
                    ip=faker.bothify(text='###.##.##.##'),
                    created_by=uuid.uuid4(),
                )
                for _ in range(num_emojis)
            ]
        with Session() as session:
            session.add_all(tags)
            session.add_all(emoji)
            session.commit()
        return {'file': file, 'tags': tags, 'emoji': emoji}

    return _create


@pytest.fixture
def created_file_with_tags_and_emoji(
    create_file_with_tags_and_emoji,
):  # pylint: disable='redefined-outer-name'
    return create_file_with_tags_and_emoji()

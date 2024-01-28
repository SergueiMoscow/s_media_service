import os
import uuid
from datetime import datetime

import pytest

from alembic import command
from alembic.config import Config
from common.settings import ROOT_DIR, settings
from common.utils import get_db_file_path
from db import models
from db.connector import AsyncSession
from db.models import Storage
from repositories.storages import create_storage
from tests.random_temp_folder import RandomTempFolder


@pytest.fixture
def apply_migrations():
    assert 'TEST' in settings.DB_DSN.upper(), 'Попытка использовать не тестовую схему.'

    alembic_cfg = Config(str(ROOT_DIR / 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', str(ROOT_DIR / 'alembic'))
    command.upgrade(alembic_cfg, 'head')

    yield command, alembic_cfg

    if settings.DB_TEST_DSN.startswith('postgresql'):
        # with AsyncSession() as session:
        #     session.execute(
        #     text(f'DROP SCHEMA IF EXISTS {settings.TEST_DATABASE_SCHEMA} CASCADE;')
        #     )
        #     session.commit()
        pass
    elif settings.DB_TEST_DSN.startswith('sqlite'):
        os.unlink(get_db_file_path(settings.DB_TEST_DSN))


@pytest.fixture
def storage(faker):
    return Storage(
        user_id=uuid.uuid4(),
        name=faker.word(),
        path=faker.word(),
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

import pytest

from db.connector import AsyncSession
from repositories.catalog import create_file, get_file_by_name


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

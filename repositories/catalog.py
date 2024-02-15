import datetime
import os

from sqlalchemy import select

from db.connector import AsyncSession
from db.models import File


async def get_file_by_name(session: AsyncSession, filename: str) -> File:
    result = await session.execute(select(File).where(File.name == filename))
    return result.scalars().first()


def create_file(session: AsyncSession, filename: str) -> File:

    file_info = os.stat(filename)
    file = File(
        name=filename,
        type=filename.rsplit('.', 1)[1],
        created=datetime.datetime.fromtimestamp(os.path.getctime(filename)),
        size=file_info.st_size,
    )
    session.add(file)
    return file


async def get_or_create_file(session: AsyncSession, filename: str) -> File:
    existing_file = await get_file_by_name(session, filename)
    if existing_file:
        return existing_file
    new_file = create_file(session, filename)
    # await session.commit()
    return new_file

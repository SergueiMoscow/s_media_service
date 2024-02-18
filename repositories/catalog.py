import datetime
import os
import uuid
from typing import List

from sqlalchemy import and_, func, or_, select

from db.connector import AsyncSession
from db.models import Emoji as EmojiModel
from db.models import File, Tag
from schemas.catalog import CreateTagParams
from schemas.storage import EmojiCount


async def get_file_by_name(session: AsyncSession, filename: str) -> File:
    result = await session.execute(select(File).where(File.name == filename))
    return result.scalars().first()


async def get_file_by_id(session: AsyncSession, file_id: uuid.UUID) -> File:
    result = await session.execute(select(File).where(File.id == file_id))
    return result.scalars().first()


async def create_file(
    session: AsyncSession, filename: str, note: str | None = None, is_public: bool | None = None
) -> File:

    file_info = os.stat(filename)
    file = File(
        name=filename,
        type=filename.rsplit('.', 1)[1],
        created=datetime.datetime.fromtimestamp(os.path.getctime(filename)),
        note=note,
        is_public=is_public,
        size=file_info.st_size,
    )
    session.add(file)
    await session.flush()
    return file


async def get_or_create_file(
    session: AsyncSession, filename: str, note: str | None = None, is_public: bool | None = None
) -> File:
    existing_file = await get_file_by_name(session, filename)
    if existing_file:
        return existing_file
    new_file = await create_file(session, filename, note, is_public)
    # await session.commit()
    return new_file


async def patch_file(
    session: AsyncSession,
    file_id: uuid.UUID,
    note: str | None = None,
    is_public: bool | None = None,
):
    file = await get_file_by_id(session, file_id)
    if note is not None:
        file.note = note
    if is_public is not None:
        file.is_public = is_public
    # await session.commit()


async def create_tag(session: AsyncSession, params: CreateTagParams):
    tag = await session.execute(
        select(Tag).where(and_(Tag.file_id == params.file_id, Tag.name == params.tag_name))
    )
    tag = tag.scalars().first()
    if tag:
        return tag
    new_tag = Tag(
        file_id=params.file_id,
        name=params.tag_name,
        created_by=params.user_id,
        ip=params.ip,
    )
    session.add(new_tag)
    await session.flush()
    return new_tag


async def toggle_emoji(session, file_id, emoji_name, ip, user_id):
    # Проверить, существует ли уже emoji для данного файла от данного пользователя или с тем же IP
    existing_emoji = await session.execute(
        select(EmojiModel).where(
            and_(
                EmojiModel.file_id == file_id,
                or_(EmojiModel.created_by == user_id, EmojiModel.ip == ip),
                EmojiModel.name == emoji_name,
            )
        )
    )
    existing_emoji = existing_emoji.scalars().first()

    if existing_emoji:
        # Если запись найдена, нужно её удалить (так как это повторный запрос)
        await session.delete(existing_emoji)
        message = 'Emoji removed'
    else:
        # Иначе - создать новую запись
        new_emoji = EmojiModel(file_id=file_id, name=emoji_name, ip=ip, created_by=user_id)
        session.add(new_emoji)
        message = 'Emoji added'

    await session.flush()
    return message


async def get_emoji_counts_by_file_id(
    session: AsyncSession, file_id: uuid.UUID
) -> List[EmojiCount]:
    # pylint: disable=not-callable
    stmt = (
        select(EmojiModel.name, func.count(EmojiModel.name).label('quantity'))
        .filter(EmojiModel.file_id == file_id)
        .group_by(EmojiModel.name)
    )
    # pylint: enable=not-callable
    result = await session.execute(stmt)
    emoji_counts = result.fetchall()
    return [EmojiCount(name=emoji_name, quantity=count) for emoji_name, count in emoji_counts]


async def get_tags_by_file_id(session: AsyncSession, file_id: uuid.UUID) -> List[str]:
    stmt = select(Tag.name, Tag.created_by, Tag.created_at).filter(Tag.file_id == file_id)
    result = await session.execute(stmt)
    tags = result.fetchall()
    return tags

import datetime
import os
import uuid
from typing import List

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from db.connector import AsyncSession
from db.models import Emoji as EmojiModel
from db.models import File, Tag
from repositories.storages import get_storage_by_id
from schemas.catalog import CatalogContentRequest, CreateTagParams
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
) -> File:
    file = await get_file_by_id(session, file_id)
    if note is not None:
        file.note = note
    if is_public is not None:
        file.is_public = is_public
    # await session.commit()
    return file


async def get_file_tags(
    session: AsyncSession, file_id: uuid.UUID, as_obj: bool = False
) -> List[str | Tag]:
    if as_obj:
        tags = await session.execute(select(Tag).where(Tag.file_id == file_id))
    else:
        tags = await session.execute(select(Tag.name).where(Tag.file_id == file_id))
    return list(tags.scalars().all())


async def create_tag(session: AsyncSession, params: CreateTagParams) -> Tag:
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


async def delete_tag_by_obj(session: AsyncSession, tag: Tag) -> None:
    await session.delete(tag)
    await session.commit()


async def delete_tag_by_file_id_and_tag_name(
    session: AsyncSession, file_id: uuid.UUID, tag_name: str
) -> None:
    tag = await session.execute(
        select(Tag).where((Tag.file_id == file_id) & (Tag.name == tag_name))
    )
    if tag := tag.scalars().first():
        await session.delete(tag)
        await session.commit()


async def toggle_emoji(session, file_id, emoji_name, ip, user_id) -> str:
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


async def get_tags_by_file_id(session: AsyncSession, file_id: uuid.UUID) -> List[Tag]:
    stmt = select(Tag.name, Tag.created_by, Tag.created_at).filter(Tag.file_id == file_id)
    result = await session.execute(stmt)
    tags = result.fetchall()
    return tags


async def get_user_tags(session: AsyncSession, user_id: uuid.UUID) -> List[Tag]:
    """
    Returns a list of unique tags created by user in all storages of server
    """
    tags = await session.execute(
        select(Tag.name, Tag.created_by).where(Tag.created_by == user_id).distinct()
    )
    return list(tags.scalars().all())


async def get_items_for_main_page(
    session: AsyncSession,
    created_before: datetime.datetime = None,  # добавляем новый параметр
    page: int = 1,
    per_page: int = 10,
) -> List[File]:
    limit = per_page
    offset = (page - 1) * per_page
    query = select(File).filter(File.is_public)
    if created_before:
        query = query.filter(File.created_at < created_before)
    files = await session.execute(
        query.options(joinedload(File.tags))
        .order_by(File.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return files.scalars().unique().all()


async def get_files_by_names(session: AsyncSession, file_names: List[str]) -> List[File]:
    """
    Возвращает список File из списка имён файлов
    """
    result = await session.execute(select(File).filter(File.name.in_(file_names)))
    return result.scalars().all()


async def get_tags_by_file_ids(session: AsyncSession, file_ids: List[str]) -> List[Tag]:
    """
    Возвращает список Tag из списка имён файлов
    """
    stmt = select(Tag).filter(Tag.file_id.in_(file_ids))
    result = await session.execute(stmt)
    tags = result.scalars().all()
    return tags


async def get_tags_by_file_names(session: AsyncSession, file_names: List[str]) -> List[Tag]:
    """
    Возвращает список Tag из списка имён файлов
    """
    stmt = select(Tag).filter(Tag.file_name.in_(file_names))
    result = await session.execute(stmt)
    tags = result.scalars().all()
    return tags


async def get_emoji_counts_by_file_ids(
    session: AsyncSession, file_ids: List[str]
) -> List[EmojiCount]:
    stmt = (
        select(EmojiModel.name, func.count(EmojiModel.name).label('quantity'))
        .filter(EmojiModel.file_id.in_(file_ids))
        .group_by(EmojiModel.name)
    )
    result = await session.execute(stmt)
    emoji_counts = result.fetchall()
    return [EmojiCount(name=emoji_name, quantity=count) for emoji_name, count in emoji_counts]


async def get_emoji_counts_by_file_names(
    session: AsyncSession, file_names: List[str]
) -> List[EmojiCount]:
    stmt = (
        select(EmojiModel.name, func.count(EmojiModel.name).label('quantity'))
        .filter(EmojiModel.file_name.in_(file_names))
        .group_by(EmojiModel.name)
    )
    result = await session.execute(stmt)
    emoji_counts = result.fetchall()
    return [EmojiCount(name=emoji_name, quantity=count) for emoji_name, count in emoji_counts]


async def get_files_by_filter(
    session: AsyncSession, storage_id: uuid.UUID, params: CatalogContentRequest
) -> List[File]:
    """
    Ищет записи File с фильтром, сортировкой и пагинацией
    """
    # сначала найдем нужное хранилище
    storage = await get_storage_by_id(session, storage_id)
    if storage is None:
        return []  # или выбросьте исключение, если хранилище должно быть гарантированно найдено

    query = select(File)

    # Фильтр по хранилищу
    query = query.filter(File.name.like(f"{storage.path}%"))

    # Фильтры по датам, если они есть
    if params.date_from is not None:
        query = query.filter(File.created_at >= params.date_from)
    if params.date_to is not None:
        query = query.filter(File.created_at <= params.date_to)

    # Фильтр по поиску в заметках
    if params.search:
        query = query.filter(File.note.like(f"%{params.search}%"))

    # Фильтр по тегам
    if params.tags:
        # Создание подзапроса для тегов
        tags_count = len(params.tags)
        files_with_all_tags = (
            select(Tag.file_id)
            .where(Tag.name.in_(params.tags))
            .group_by(Tag.file_id)
            .having(func.count(Tag.file_id) == tags_count)
            .subquery()
        )
        query = query.filter(File.id.in_(select(files_with_all_tags.c.file_id)))

    # Фильтр по публичности файла
    if params.public is not None:
        query = query.filter(File.is_public == params.public)

    # Сортировка
    if params.sort_direction == 'desc':
        query = query.order_by(getattr(File, params.sort).desc())
    else:
        query = query.order_by(getattr(File, params.sort))

    # Пагинация
    offset = (params.page - 1) * params.per_page
    query = query.offset(offset).limit(params.per_page)

    query = query.options(selectinload(File.tags)).options(selectinload(File.emoji))
    result = await session.execute(query)
    return result.scalars().all()


async def get_total_count_by_filter(
        session: AsyncSession, storage_id: uuid.UUID, params: CatalogContentRequest
) -> int:
    """
    Считает общее количество записей для функции get_files_by_filter.
    Условия те же, но без пагинации и сортировки.
    Возвращает количество, удовлетворяющее условию.
    """
    # сначала найдем нужное хранилище
    storage = await get_storage_by_id(session, storage_id)
    if storage is None:
        return 0  # или выбросьте исключение, если хранилище должно быть гарантированно найдено

    query = select(func.count(File.id))

    # Фильтр по хранилищу
    query = query.filter(File.name.like(f"{storage.path}%"))

    # Фильтры по датам, если они есть
    if params.date_from is not None:
        query = query.filter(File.created_at >= params.date_from)
    if params.date_to is not None:
        query = query.filter(File.created_at <= params.date_to)

    # Фильтр по поиску в заметках
    if params.search:
        query = query.filter(File.note.like(f"%{params.search}%"))

    # Фильтр по тегам
    if params.tags:
        query = query.join(Tag, File.id == Tag.file_id)
        # Ищем файлы со всеми указанными тегами
        for tag in params.tags:
            query = query.filter(Tag.name == tag)

    # Фильтр по публичности файла
    if params.public is not None:
        query = query.filter(File.is_public == params.public)

    result = await session.execute(query)
    return result.scalar()

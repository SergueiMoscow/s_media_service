"""
Каталог - это инфо о файлах в БД.
Без привязки к storage.
Используется в информативных целях
Для связки с Front используется id (uuid)
Ключ - полное имя файла с путём (для бэка)
"""
import os

from common.exceptions import BadRequest
from db.connector import AsyncSession
from repositories.catalog import (
    create_file,
    create_tag,
    get_emoji_counts_by_file_id,
    get_file_by_id,
    get_file_by_name,
    get_tags_by_file_id,
    patch_file,
    toggle_emoji,
)
from repositories.storages import get_storage_by_id
from schemas.catalog import CatalogFileRequest, CatalogFileResponseResult, CreateTagParams
from schemas.storage import EmojiCount


class CatalogFile:
    def __init__(self, filename):
        self.filename = filename

    def get_file_info(self) -> CatalogFileResponseResult:
        pass

    def get_note(self) -> str | None:
        return None

    def get_tags(self) -> list[str]:
        return []

    def get_emoji(self) -> list[EmojiCount]:
        return []


async def file_add_data_service(data: CatalogFileRequest) -> CatalogFileResponseResult:
    async with AsyncSession() as session:
        if data.id:
            file = await get_file_by_id(session, data.id)
        # folder_path может быть '' если file в корне хранилища
        elif data.filename and data.storage_id and isinstance(data.folder_path, str):
            storage = await get_storage_by_id(session, data.storage_id)
            full_path = os.path.join(storage.path, data.folder_path, data.filename)
            file = await get_file_by_name(session, full_path)
        else:
            raise BadRequest(error_message='file_add_data_service exception')
        # data.note
        if file is None:
            file = await create_file(session, full_path, data.note, data.is_public)
        else:
            if data.note:
                await patch_file(session, file.id, data.note, data.is_public)
        result = CatalogFileResponseResult(
            id=file.id,
            note=data.note,
        )
        result.note = data.note
        result.is_public = data.is_public
        # data.tag
        if data.tag:
            create_tag_params = CreateTagParams(
                file_id=file.id,
                tag_name=data.tag,
                user_id=data.user_id,
                ip=data.ip,
            )
            await create_tag(session, create_tag_params)
            result.tags.append(data.tag)
        # data.emoji
        if data.emoji:
            await toggle_emoji(session, file.id, data.emoji, data.ip, data.user_id)
        result.emoji = await get_emoji_counts_by_file_id(session, file.id)
        await session.commit()
        return result


async def get_file_data_from_catalog_by_fullname(filename: str) -> dict | None:
    async with AsyncSession() as session:
        file = await get_file_by_name(session, filename)
        if file is None:
            return None
        tags = await get_tags_by_file_id(session, file.id)
        emoji = await get_emoji_counts_by_file_id(session, file.id)
    return {
        'note': file.note,
        'is_public': file.is_public,
        'tags': tags,
        'emoji': emoji,
    }

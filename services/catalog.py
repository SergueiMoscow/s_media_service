"""
Каталог - это инфо о файлах в БД.
Без привязки к storage.
    (Storage может быть найден по полному пути файла для проверки прав на изменение полей:
    note, is_public, или тегов)
Для связки с Front используется id (uuid) или storage_id + folder + filename
Ключ - полное имя файла с путём (для бэка)
Теоретически один файл может быть в нескольких storage (если они вложены), но за "правильный"
    берётся storage с самым длинным путём
"""
import datetime
import os
import uuid
from typing import List

from common.exceptions import BadRequest, NotFound
from db import models
from db.connector import AsyncSession
from repositories.catalog import (
    create_file,
    create_tag,
    delete_tag_by_file_id_and_tag_name,
    get_emoji_counts_by_file_id,
    get_file_by_id,
    get_file_by_name,
    get_file_tags,
    get_items_for_main_page,
    get_tags_by_file_id,
    get_user_tags,
    patch_file,
    toggle_emoji,
)
from repositories.storages import find_storage_by_path, get_storage_by_id
from schemas.catalog import (
    CatalogFileRequest,
    CatalogFileResponseResult,
    CreateTagParams,
    ListCatalogFilesResponse,
)
from schemas.storage import EmojiCount
from services.storage_file import ResponseFile


class CatalogFileBase:
    def __init__(self):
        self.data: CatalogFileRequest | None = None
        self.file: models.File | None = None
        self.storage: models.Storage | None = None
        self.filename: str | None = None
        self.result: CatalogFileResponseResult | None = None

    @classmethod
    async def create(cls, data: CatalogFileRequest):
        """
        Метод создания объекта
        """
        self = cls()
        self.data = data
        await self.get_file()
        return self

    async def get_file(self):
        """
        Подгружает объект File в self.file или None
        """
        async with AsyncSession() as session:
            if self.data.id:
                self.file = await get_file_by_id(session, self.data.id)
                self.filename = self.file.name
            elif (
                self.data.filename
                and self.data.storage_id
                and isinstance(self.data.folder_path, str)
            ):
                # folder_path может быть '' если file в корне хранилища
                await self._get_storage()
                # TO_DO: Убрать начальные слеши '/' из folder_path
                full_path = os.path.join(
                    self.storage.path, self.data.folder_path, self.data.filename
                )
                self.filename = full_path
                self.file = await get_file_by_name(session, full_path)
            else:
                raise BadRequest(error_message='file_add_data_service exception: no file id')
            if self.file:
                self.result = CatalogFileResponseResult(id=self.file.id)

    async def _get_storage(self):
        """
        Подгружает объект Storage в self.storage
        Нужен для проверки, может ли пользователь вносить изменения
        """
        if isinstance(self.data.storage_id, uuid.UUID):
            async with AsyncSession() as session:
                self.storage = await get_storage_by_id(session, self.data.storage_id)
                return
        async with AsyncSession() as session:
            self.storage = await find_storage_by_path(session, self.file.filename)

        if not isinstance(self.storage, models.Storage):
            raise NotFound(
                error_message=f'CatalogFileBase: storage {self.data.storage_id} not found'
            )

    async def _user_has_permission(self):
        """
        Менять note, is_public, tags может только хозяин хранилища
        """
        if self.data.note or self.data.tag or self.data.is_public is not None:
            self.storage = self._get_storage()
            return self.data.user_id == self.storage.user_id
        return True


class CatalogFileChange(CatalogFileBase):
    async def change_data(self) -> CatalogFileResponseResult:
        if self._user_has_permission():
            await self._change_file()
            await self._change_tags()
            await self._change_emoji()
        return self.result

    async def _change_file(self):
        """
        Создаёт или меняет запись File (таблица files)
        Все проверки на добавление/изменение должны быть пройдены.
        """
        async with AsyncSession() as session:
            if self.file is None:
                self.file = await create_file(
                    session, self.filename, self.data.note, self.data.is_public
                )
            else:
                self.file = await patch_file(
                    session,
                    file_id=self.file.id,
                    note=self.data.note if self.data.note is not None else None,
                    is_public=self.data.is_public if self.data.is_public is not None else None,
                )
            await session.commit()
        self.result = CatalogFileResponseResult(
            id=self.file.id,
            note=self.file.note,
            is_public=self.file.is_public,
        )

    async def _change_tags(self):
        if self.data.tags:
            for tag in self.data.tags:
                async with AsyncSession() as session:
                    exists_tags = await get_file_tags(session, self.file.id)
                    if tag not in exists_tags:
                        create_tag_params = CreateTagParams(
                            file_id=self.file.id,
                            tag_name=tag,
                            user_id=self.data.user_id,
                            ip=self.data.ip,
                        )
                        await create_tag(session, create_tag_params)
                        await session.commit()
                        self.result.tags.append(tag)

            if self.data.remove_tag in exists_tags:
                async with AsyncSession() as session:
                    await delete_tag_by_file_id_and_tag_name(
                        session=session,
                        file_id=self.file.id,
                        tag_name=self.data.remove_tag,
                    )
                    await session.commit()

    async def _change_emoji(self):
        if self.data.emoji:
            async with AsyncSession() as session:
                await toggle_emoji(
                    session, self.file.id, self.data.emoji, self.data.ip, self.data.user_id
                )
                await session.commit()
            async with AsyncSession() as session:
                self.result.emoji = await get_emoji_counts_by_file_id(session, self.file.id)
                await session.commit()


class CatalogFileRead(CatalogFileBase):
    def get_note(self) -> str | None:
        return None

    def get_tags(self) -> list[str]:
        return []

    def get_emoji(self) -> list[EmojiCount]:
        return []


async def file_add_data_service(data: CatalogFileRequest) -> CatalogFileResponseResult:
    catalog_file_change = await CatalogFileChange.create(data)
    return await catalog_file_change.change_data()


async def get_file_data_from_catalog_by_fullname(filename: str) -> dict | None:
    async with AsyncSession() as session:
        file = await get_file_by_name(session, filename)
        if file is None:
            return None
        tags_tuples = await get_tags_by_file_id(session, file.id)
        emoji = await get_emoji_counts_by_file_id(session, file.id)
        tags = [tag_tuple[0] for tag_tuple in tags_tuples]
    return {
        'note': file.note,
        'is_public': file.is_public,
        'tags': tags,
        'emoji': emoji,
    }


async def get_user_tags_service(user_id: uuid.UUID) -> List[str]:
    async with AsyncSession() as session:
        return await get_user_tags(session, user_id)


class ListCatalogFileResponse:
    pass


async def get_items_for_main_page_service(
    created_before: datetime.datetime = None, **kwargs
) -> ListCatalogFilesResponse:
    async with AsyncSession() as session:
        files = await get_items_for_main_page(session, created_before=created_before, **kwargs)
        result = []
        for file in files:
            emoji_count = await get_emoji_counts_by_file_id(session, file.id)
            tags = await get_tags_by_file_id(session, file.id)
            result_file = CatalogFileResponseResult(
                id=file.id,
                is_public=file.is_public,
                note=file.note,
                size=file.size,
                tags=[tag.name for tag in tags],
                emoji=emoji_count,
                created_at=file.created_at,
            )
            result.append(result_file)
        return ListCatalogFilesResponse(files=result)


async def get_catalog_file_service(file_id: uuid.UUID, width: int | None = None):
    async with AsyncSession() as session:
        file = await get_file_by_id(session, file_id=file_id)
    result = ResponseFile(file.name, width)
    return await result.get_preview()

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
from collections import defaultdict
from typing import List, Tuple

from common.exceptions import BadRequest, NotFound
from common.settings import settings
from db import models
from db.connector import AsyncSession
from db.models import File
from repositories.catalog import (
    create_file,
    create_tag,
    delete_tag_by_file_id_and_tag_name,
    get_emoji_counts_by_file_id,
    get_emoji_counts_by_file_ids,
    get_file_by_id,
    get_file_by_name,
    get_file_tags,
    get_files_by_filter,
    get_files_by_names,
    get_items_for_main_page,
    get_tags_by_file_id,
    get_tags_by_file_ids,
    get_user_tags,
    patch_file,
    toggle_emoji, get_total_count_by_filter,
)
from repositories.storages import find_storage_by_path, get_storage_by_id
from schemas.catalog import (
    CatalogContentRequest,
    CatalogFileRequest,
    CatalogFileResponseResult,
    CreateTagParams,
    ListCatalogFilesResponse, ListCatalogFilesResponseWithPagination,
)
from schemas.storage import EmojiCount, StorageFile, Pagination
from services.CacheManager import CacheManager
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
            type=self.file.type,
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

            # Теперь обрабатываем те тэги, которые нужно удалить
            # Случай, когда приходит list
            for tag in exists_tags:
                if tag not in self.data.tags:
                    async with AsyncSession() as session:
                        await delete_tag_by_file_id_and_tag_name(
                            session, file_id=self.file.id, tag_name=tag
                        )
                        await session.commit()

            # Случай, если есть remove_tag
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


async def get_files_data_from_catalog_by_names_list(
    storage_files: List[StorageFile],
):
    # Получаем все объекты списка
    model_files = await get_files_by_names_service([file.full_path for file in storage_files])
    # Создаем словарь {file.name: file}
    file_catalog_dict = {file.name: file for file in model_files}

    async with AsyncSession() as session:
        # Берем все перечисленные теги для файлов из file_catalog_data
        tags = await get_tags_by_file_ids(session, [file.id for file in model_files])
        # Берем все перечисленные эмодзи для файлов из file_catalog_data
        emoji = await get_emoji_counts_by_file_ids(session, [file.id for file in model_files])

    tags_dict = defaultdict(list)
    emoji_dict = defaultdict(list)

    for tag in tags:
        tags_dict[tag.file_id].append(tag.name)

    for e in emoji:
        emoji_dict[e.file_id].append(e)

    # Перебираем список nested_files и дополняем его свойствами
    for nf in storage_files:
        file_db = file_catalog_dict.get(nf.full_path)
        if file_db is not None:
            nf.note = file_db.note
            nf.is_public = file_db.is_public
            nf.tags = tags_dict.get(file_db.id, [])
            nf.emoji = emoji_dict.get(file_db.id, [])

    return storage_files


async def get_user_tags_service(user_id: uuid.UUID) -> List[str]:
    async with AsyncSession() as session:
        return await get_user_tags(session, user_id)


class ListCatalogFileResponse:
    def __init__(self):
        self.storage_id: uuid.UUID | None = None
        self.params: CatalogContentRequest | None = None
        self.response_result = None
        self.response_pagination = None

    async def get_files(
            self,
            storage_id: uuid.UUID,
            params: CatalogContentRequest
    ) -> Tuple[List[CatalogFileResponseResult], Pagination]:
        self.storage_id = storage_id
        self.params = params
        async with AsyncSession() as session:
            files_list = await get_files_by_filter(session, storage_id, params)
            result = await self._convert_files_to_catalog_file_response_result(session, files_list)
        pagination = await self._create_pagination()
        return result, pagination

    async def _convert_files_to_catalog_file_response_result(
        self,
        session: AsyncSession,
        files: List[File]
    ) -> List[CatalogFileResponseResult]:
        result = []
        for file in files:
            emoji_count = await get_emoji_counts_by_file_id(session, file.id)
            result.append(CatalogFileResponseResult(
                id=file.id,
                is_public=file.is_public,
                type=file.type,
                note=file.note,
                size=file.size,
                tags=[tag.name for tag in file.tags],
                emoji=emoji_count,
                created_at=file.created_at
            ))
        self.response_result = result
        return result

    async def _create_pagination(self) -> Pagination:
        async with AsyncSession() as session:
            total_items = await get_total_count_by_filter(session, self.storage_id, self.params)
        self.response_pagination = Pagination(
            page=self.params.page,
            per_page=self.params.per_page,
            items=total_items
        )
        return self.response_pagination


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
                type=file.type,
                size=file.size,
                tags=[tag.name for tag in tags],
                emoji=emoji_count,
                created_at=file.created_at,
            )
            result.append(result_file)
        return ListCatalogFilesResponse(files=result)


async def get_catalog_file_service(file_id: uuid.UUID, width: int = settings.PREVIEW_WIDTH):
    async with AsyncSession() as session:
        file = await get_file_by_id(session, file_id=file_id)
    result = ResponseFile(
        filename=file.name,
        cache_manager=CacheManager(file.name),
        width=width
    )
    return await result.get_preview()


async def get_files_by_names_service(file_names: list):
    async with AsyncSession() as session:
        return await get_files_by_names(session=session, file_names=file_names)

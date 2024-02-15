"""
Каталог - это инфо о файлах в БД.
Без привязки к storage.
Используется в информативных целях
Для связки с Front используется id (uuid)
Ключ - полное имя файла с путём (для бэка)
"""
from schemas.catalog import CatalogFileInfo
from schemas.storage import Emoji


class CatalogFile:
    def __init__(self, filename):
        self.filename = filename

    def get_file_info(self) -> CatalogFileInfo:
        pass

    def get_note(self) -> str | None:
        return None

    def get_tags(self) -> list[str]:
        return []

    def get_emoji(self) -> list[Emoji]:
        return []

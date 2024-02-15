import uuid

from pydantic import BaseModel

from schemas.storage import Emoji


class CatalogFileInfo(BaseModel):
    """
    То, что возвращаем на FrontEnd
    """

    id: uuid.UUID
    note: str | None = None
    tags: list[str] = []
    emoji: list[Emoji] = []

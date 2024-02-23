import os
from urllib.parse import urlparse
from uuid import UUID

from fastapi import Header, HTTPException


def get_db_file_path(dsn):
    parsed = urlparse(dsn)
    return os.path.normpath(parsed.path)


async def get_header_user_id(x_user_id: str = Header(None)):
    if not x_user_id:
        return None
    try:
        # Try to convert the header to a UUID
        return UUID(x_user_id)
    except ValueError as e:
        # The header is not a valid UUID
        raise HTTPException(status_code=400, detail=f'Invalid X-USER-ID header, {e}') from e

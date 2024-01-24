import os
from urllib.parse import urlparse


def get_db_file_path(dsn):
    parsed = urlparse(dsn)
    return os.path.normpath(parsed.path)

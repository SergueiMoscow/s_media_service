import sys
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from common.settings import settings


def get_dsn():
    if 'pytest' in sys.modules:
        if 'TEST' not in settings.DB_TEST_DSN.upper() or settings.DB_TEST_DSN != settings.DB_DSN:
            # Создание временного файла для базы данных
            with tempfile.NamedTemporaryFile(
                prefix='test', suffix='.sqlite3', delete=False
            ) as temp_db_file:
                settings.DB_TEST_DSN = f'sqlite:///{temp_db_file.name}'
                settings.DB_DSN = settings.DB_TEST_DSN
    return settings.DB_DSN


db_url = get_dsn()

engine = create_engine(
    get_dsn(),
    echo=True,
    pool_size=6,
    max_overflow=10,
)
engine.connect()
session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

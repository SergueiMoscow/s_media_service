from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent
CACHE_COLLAGE_FILE = '.folder.jpg'
CACHE_COLLAGE_INFO = '.folder.json'


class Settings(BaseSettings):
    ROOT_DIR: Path = ROOT_DIR
    DB_DSN: str = ''
    DB_TEST_DSN: str = ''
    DATABASE_SCHEMA: str = 'public'
    KEY: str = ''
    SWAGGER_URL: str | None = None
    REDOC_URL: str | None = None
    PER_PAGE: int = 10
    # For cache
    CACHE_DIR: str = '/tmp/s_media_service'
    THUMBNAIL_WIDTH: int = 200
    PREVIEW_WIDTH: int = 400

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8',
        extra='allow',
    )


settings = Settings()

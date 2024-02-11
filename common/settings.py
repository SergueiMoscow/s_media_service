from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    ROOT_DIR: Path = ROOT_DIR
    DB_DSN: str = ''
    DB_TEST_DSN: str = ''
    DATABASE_SCHEMA: str = 'public'
    KEY: str = ''
    SWAGGER_URL: str | None = None
    REDOC_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8',
        extra='allow',
    )


settings = Settings()

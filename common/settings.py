from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    ROOT_DIR: Path = ROOT_DIR
    DB_DSN: str = ''
    DB_TEST_DSN: str = ''
    KEY: str = ''

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8',
        extra='allow',
    )


settings = Settings()

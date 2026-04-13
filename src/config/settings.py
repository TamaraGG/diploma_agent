from pathlib import Path
from pprint import pprint

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, EmailStr, Field, BaseModel

BASE_DIR = Path(__file__).parent.parent.parent

class GigaChatSettings(BaseModel):
    model: str = "GigaChat-Pro"


class DatabaseSettings(BaseModel):
    user: str
    password: SecretStr
    db_name: str
    port: int = 5432
    host: str = "localhost"
    collection_name: str = "documents"

    @property
    def sqlalchemy_url(self) -> str:
        return (f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@"
                f"{self.host}:{self.port}/{self.db_name}")


class ScraperSettings(BaseModel):
    timeout: int = Field(default=30, ge=1)
    retry_count: int = 3
    download_folder: Path = Field(default=BASE_DIR / "data" / "downloads")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding='utf-8',
        env_nested_delimiter="__",
        extra="ignore"
    )

    app_name: str = "Diploma Agent"

    gigachat_api_key: SecretStr | None = None

    gigachat: GigaChatSettings = GigaChatSettings()
    db: DatabaseSettings
    scraper: ScraperSettings = ScraperSettings()


try:
    settings = AppSettings()
except Exception as e:
    print(f"Ошибка валидации конфига: {e}")
    raise


from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:ChuwKo95U6sK5fJr@db.gpcygulldcccdrsnnxmr.supabase.co:5432/postgres"

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

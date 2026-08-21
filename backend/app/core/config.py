from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str ="postgresql://postgres:Gt7ZcKZB1KamI0Dw@db.gpcygulldcccdrsnnxmr.supabase.co:5432/postgres"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
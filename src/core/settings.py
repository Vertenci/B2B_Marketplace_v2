from pydantic import PostgresDsn, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    ALLOWED_ORIGINS: str

    ADMIN_EMAIL: EmailStr
    ADMIN_PASSWORD: str
    ADMIN_SECRET_KEY: str

    APP_SECRET_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    PGADMIN_DEFAULT_EMAIL: str = "admin@admin.com"
    PGADMIN_DEFAULT_PASSWORD: str = "admin"

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    MINIO_BUCKET_NAME: str
    MINIO_SECURE: bool
    MINIO_PUBLIC_URL: str

    @property
    def MINIO_URL(self) -> str:
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()

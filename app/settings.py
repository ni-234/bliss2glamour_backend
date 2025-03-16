from os.path import dirname, realpath

from pydantic_settings import BaseSettings, SettingsConfigDict


model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    validate_default=False,
    extra="ignore",
)


class AppSettings(BaseSettings):
    model_config = model_config
    ROOT_DIR: str = dirname(realpath(__file__))
    APP_NAME: str
    APP_DESCRIPTION: str
    APP_VERSION: str
    LICENSE_NAME: str | None = None
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None
    OPENAPI_URL: str = "/openapi.json"
    CORS_ORIGINS: list[str] = ["*"]
    ALLOWED_METHODS: list[str] = ["GET", "POST", "PATCH", "DELETE"]


class CryptSettings(BaseSettings):
    model_config = model_config
    ALGORITHM: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class DatabaseSettings(BaseSettings):
    model_config = model_config
    pass


class SQLiteSettings(DatabaseSettings):
    SQLITE_URI: str = "./sql_app.db"
    SQLITE_SYNC_PREFIX: str = "sqlite:///"
    SQLITE_ASYNC_PREFIX: str = "sqlite+aiosqlite:///"


class MySQLSettings(DatabaseSettings):
    MYSQL_USER: str = "username"
    MYSQL_PASSWORD: str = "password"
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 5432
    MYSQL_DB: str = "dbname"
    MYSQL_URI: str = (
        f"{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_SERVER}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    MYSQL_SYNC_PREFIX: str = "mysql://"
    MYSQL_ASYNC_PREFIX: str = "mysql+aiomysql://"
    MYSQL_URL: str | None = None


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    POSTGRES_URI: str = (
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    POSTGRES_URL: str | None = None


class FirstUserSettings(BaseSettings):
    model_config = model_config
    ADMIN_NAME: str = "admin"
    ADMIN_FIRST_NAME: str = "Admin"
    ADMIN_LAST_NAME: str = "User"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"


class Settings(AppSettings, CryptSettings, SQLiteSettings, FirstUserSettings):
    pass


settings = Settings()

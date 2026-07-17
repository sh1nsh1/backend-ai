from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseEnv(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Redis(BaseEnv):
    """Конфигурация Redis"""

    url: str

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class Postgres(BaseEnv):
    """Конфигурация базы данных PostgreSql"""

    drivername: str = "postgresql+asyncpg"
    user: str
    password: str
    host: str
    port: int
    db: str

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class EmailEnv(BaseEnv):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str

    model_config = SettingsConfigDict(env_prefix="EMAIL_")


class LogEnv(BaseEnv):
    file: str = ""

    model_config = SettingsConfigDict(env_prefix="LOG_")


class DeepSeekEnv(BaseEnv):
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"

    model_config = SettingsConfigDict(env_prefix="DEEPSEEK_")


class Config:
    redis: Redis = Redis()  # type: ignore
    postgres: Postgres = Postgres()  # type: ignore
    email: EmailEnv = EmailEnv()  # type: ignore
    log: LogEnv = LogEnv()  # type: ignore
    deepseek: DeepSeekEnv = DeepSeekEnv()  # type: ignore


config = Config()

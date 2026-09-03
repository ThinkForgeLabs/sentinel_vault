from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # General
    app_name: str = "Sentinel Vault"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-random-64-char-string"

    # Database
    database_url: str = (
        "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel_vault"
    )
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_root: str = "./data/recordings"
    upload_root: str = "./data/uploads"
    models_dir: str = "./data/models"
    encryption_enabled: bool = True
    segment_duration_minutes: int = 15

    # MQTT (optional bridge for external MQTT/TAK integration)
    mqtt_enabled: bool = False
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_tls_enabled: bool = False
    mqtt_tls_insecure: bool = False
    mqtt_topic_alerts: str = "sentinelvault/alerts"
    # CoT (Cursor-on-Target) publishes plain XML text on this topic, not JSON
    # — the format PyTAK / FreeTAKServer / most TAK MQTT bridges expect.
    mqtt_topic_cot: str = "cot"
    cot_type: str = "a-u-G"
    cot_stale_seconds: float = 60.0

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Auth
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

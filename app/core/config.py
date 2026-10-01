import os
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# secret 檔名 -> 對應的設定欄位（環境變數優先於 secret 檔）
SECRET_FILE_FIELDS = {
    "db_username": "DB_USERNAME",
    "db_password": "DB_PASSWORD",
    "aws_access_key_id": "AWS_ACCESS_KEY_ID",
    "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY",
}


def _resolve_secrets_dir(values: dict) -> Path:
    """優先順序：env/設定值 > /run/secrets (docker) > ./secrets (本機開發)"""
    configured = values.get("SECRETS_DIR") or os.getenv("SECRETS_DIR")
    if configured:
        return Path(configured)
    docker_secrets = Path("/run/secrets")
    if docker_secrets.is_dir():
        return docker_secrets
    return Path("./secrets")


class AppConfig(BaseSettings):
    # 優先順序：環境變數 > .env.local > secret 檔 > 預設值
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    APP_NAME: str = "kotoba"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SERVER_PORT: int = 8000

    SECRETS_DIR: str = ""

    # database：直接給 DATABASE_URL 時優先使用（雲端），否則由下列欄位組出（地端）
    DATABASE_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "kotoba"
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_POOL_MIN_SIZE: int = 1
    DB_POOL_MAX_SIZE: int = 5

    # aws：AWS_ENDPOINT_URL 留空 = 連真的 AWS；地端指向 LocalStack
    AWS_ENDPOINT_URL: str = ""
    AWS_DEFAULT_REGION: str = "ap-northeast-1"
    # 只在連 LocalStack 時使用（由 secret 檔提供）；連真的 AWS 時由 IAM Role 自動提供，不需設定
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    ANALYZE_QUEUE_NAME: str = "analyze-queue"
    DB_WRITER_QUEUE_NAME: str = "db-writer-queue"
    STATS_QUEUE_NAME: str = "stats-queue"
    ANALYZED_TOPIC_NAME: str = "comment-analyzed"

    # llm：fake = 不呼叫 Bedrock，回傳固定格式的假結果（地端開發用）
    LLM_PROVIDER: Literal["fake", "bedrock"] = "fake"

    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _load_secrets(cls, values: dict) -> dict:
        secrets_dir = _resolve_secrets_dir(values)
        for filename, field in SECRET_FILE_FIELDS.items():
            if values.get(field):  # 已由環境變數提供
                continue
            for candidate in (secrets_dir / filename, secrets_dir / f"{filename}.txt"):
                if candidate.is_file():
                    values[field] = candidate.read_text().strip()
                    break
        return values

    @model_validator(mode="after")
    def _build_database_url(self):
        if not self.DATABASE_URL:
            auth = ""
            if self.DB_USERNAME:
                auth = quote(self.DB_USERNAME, safe="")
                if self.DB_PASSWORD:
                    auth += ":" + quote(self.DB_PASSWORD, safe="")
                auth += "@"
            self.DATABASE_URL = f"postgresql://{auth}{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return self


app_config = AppConfig()

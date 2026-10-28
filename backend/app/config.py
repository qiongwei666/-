"""应用配置：统一从环境变量 / backend/.env 读取。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend 目录，用于定位 .env
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """项目运行配置。字段均可在 .env 中覆盖。"""

    APP_NAME: str = "品寻 · 推荐电商平台"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # JWT 配置
    SECRET_KEY: str = "ecommerce-rec-demo-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 数据库配置（默认与本项目 docker-compose / 本地 MySQL 一致）
    DATABASE_URL: str = (
        "mysql+pymysql://root:276367@127.0.0.1:3306/ecommerce?charset=utf8mb4"
    )
    DATABASE_ECHO: bool = False

    # Redis 配置
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_CONNECT_TIMEOUT: float = 0.25
    REDIS_SOCKET_TIMEOUT: float = 0.35
    RECOMMEND_CACHE_TTL: int = 60 * 60 * 6

    # CORS，多个源用英文逗号分隔
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """把逗号分隔的 CORS 配置转换为列表。"""
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """缓存配置对象，避免重复解析 .env。"""
    return Settings()


settings = get_settings()

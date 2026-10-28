"""Redis 客户端：懒加载，连接失败不影响主流程。"""

from __future__ import annotations

import logging

import redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """获取全局 Redis 客户端。

    使用较短的连接 / 读取超时，保证推荐接口在 Redis 故障时能快速降级。
    """
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            retry_on_timeout=False,
            protocol=2,
        )
    return _client


def is_redis_available() -> bool:
    """健康检查，供 /api/health 使用。"""
    try:
        return bool(get_redis().ping())
    except (RedisError, OSError):
        return False


def close_redis() -> None:
    """应用关闭时释放连接池。"""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:  # pragma: no cover - 关闭异常无需影响退出
            logger.debug("关闭 Redis 连接失败", exc_info=True)
        _client = None

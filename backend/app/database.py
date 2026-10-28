"""数据库连接与会话管理。"""

import re
from collections.abc import Generator

import pymysql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# pool_pre_ping 防止 MySQL 空闲连接失效；pool_recycle 定期回收连接
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DATABASE_ECHO,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求使用独立会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database() -> None:
    """MySQL 下自动创建数据库，方便 seed 和首次启动。"""
    url = make_url(settings.DATABASE_URL)
    if not url.drivername.startswith("mysql") or not url.database:
        return

    database = url.database
    # 数据库名只允许字母、数字、下划线，避免拼接注入
    if not re.fullmatch(r"[A-Za-z0-9_]+", database):
        raise ValueError(f"非法数据库名: {database}")

    conn = pymysql.connect(
        host=url.host or "127.0.0.1",
        port=url.port or 3306,
        user=url.username or "root",
        password=url.password or "",
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()


def init_db() -> None:
    """创建数据库与全部业务表（幂等）。"""
    ensure_database()
    # 延迟导入，确保所有模型已注册到 Base.metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

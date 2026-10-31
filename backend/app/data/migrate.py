"""非破坏性表结构同步。

用于已有数据库升级：只补建缺失的表、列和索引，不会删除或重建已有数据。
首次部署需要演示数据时使用 ``python -m app.data.seed``（会清空业务表）；
之后更新代码直接启动服务即可，应用启动时会自动执行本同步。
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateColumn

from app.database import Base, engine, init_db

logger = logging.getLogger(__name__)


def _add_column_ddl(table, column) -> str:
    """生成跨方言的 ALTER TABLE ... ADD COLUMN 语句。"""
    preparer = engine.dialect.identifier_preparer
    column_ddl = str(CreateColumn(column).compile(dialect=engine.dialect))
    return f"ALTER TABLE {preparer.format_table(table)} ADD COLUMN {column_ddl}"


def sync_schema() -> list[str]:
    """把 ORM 定义增量同步到数据库，返回实际执行的变更列表。"""
    # 延迟导入，确保全部模型已注册到 Base.metadata
    from app import models  # noqa: F401

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing_tables = [
        table.name
        for table in Base.metadata.sorted_tables
        if table.name not in existing_tables
    ]

    # 创建缺失的表；已有表和数据保持不变
    init_db()

    changes = [f"新建表 {name}" for name in missing_tables]
    inspector = inspect(engine)

    for table in Base.metadata.sorted_tables:
        existing_columns = {
            column["name"] for column in inspector.get_columns(table.name)
        }
        for column in table.columns:
            if column.name in existing_columns:
                continue
            if not column.nullable and column.server_default is None:
                # MySQL 无法给已有行填充非空且无默认值的列，跳过并提示手动处理
                logger.warning(
                    "跳过非空列 %s.%s：缺少 server_default，需手动迁移",
                    table.name,
                    column.name,
                )
                continue
            with engine.begin() as conn:
                conn.execute(text(_add_column_ddl(table, column)))
            changes.append(f"{table.name} 新增列 {column.name}")

    for table in Base.metadata.sorted_tables:
        existing_indexes = {
            index["name"] for index in inspector.get_indexes(table.name)
        }
        for index in table.indexes:
            if index.name in existing_indexes:
                continue
            try:
                index.create(bind=engine, checkfirst=True)
            except Exception as exc:  # pragma: no cover - 索引创建失败不阻断启动
                logger.warning("创建索引 %s 失败：%s", index.name, exc)
                continue
            changes.append(f"{table.name} 新增索引 {index.name}")

    return changes


def main() -> None:
    changes = sync_schema()
    if changes:
        for change in changes:
            print(f"- {change}")
        print(f"[migrate] 完成，共 {len(changes)} 项变更，已有数据未删除。")
    else:
        print("[migrate] 数据库结构已是最新，无需变更。")


if __name__ == "__main__":
    main()

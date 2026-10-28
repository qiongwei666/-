"""统一 API 响应工具。"""

from typing import Any


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """构造成功响应，保持前后端统一契约。"""
    return {"code": 0, "message": message, "data": data}


def failure(code: int, message: str) -> dict[str, Any]:
    """构造业务失败响应。"""
    return {"code": code, "message": message, "data": None}

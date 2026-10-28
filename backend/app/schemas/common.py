"""通用响应模型。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应结构：code=0 表示成功。"""

    code: int = 0
    message: str = "ok"
    data: T | None = None

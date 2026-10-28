"""推荐接口 Schema。"""

from pydantic import BaseModel

from app.schemas.product import ProductOut


class RecommendResponse(BaseModel):
    """推荐结果；strategy 标识实际使用的推荐策略。"""

    items: list[ProductOut]
    strategy: str
    scene: str | None = None

"""分类与商品 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    """分类树节点。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None = None
    children: list["CategoryOut"] = Field(default_factory=list)


class ProductOut(BaseModel):
    """商品对外结构。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: float
    stock: int
    category_id: int
    category_name: str = ""
    sales: int
    image_url: str
    status: str
    created_at: datetime


class ProductPage(BaseModel):
    """商品分页结果。"""

    items: list[ProductOut]
    total: int
    page: int
    size: int

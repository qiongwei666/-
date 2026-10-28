"""购物车 Schema。"""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductOut


class CartAddRequest(BaseModel):
    """加入购物车。"""

    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class CartUpdateRequest(BaseModel):
    """修改购物车数量。"""

    quantity: int = Field(ge=1, le=99)


class CartItemOut(BaseModel):
    """购物车条目。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    subtotal: float
    product: ProductOut


class CartOut(BaseModel):
    """购物车整体信息。"""

    items: list[CartItemOut]
    total_quantity: int
    total_amount: float

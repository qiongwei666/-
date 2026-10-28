"""订单 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderItemOut(BaseModel):
    """订单明细。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str = ""
    image_url: str = ""
    quantity: int
    price: float
    subtotal: float


class OrderOut(BaseModel):
    """订单详情。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    total_amount: float
    status: str
    total_quantity: int
    created_at: datetime
    items: list[OrderItemOut]

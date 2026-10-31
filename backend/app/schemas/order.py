"""订单 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderCreateIn(BaseModel):
    """下单请求：可选指定收货地址。"""

    address_id: int | None = Field(default=None, gt=0)


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
    tracking_no: str | None = None
    shipped_at: datetime | None = None
    return_type: str | None = None
    return_reason: str | None = None
    receiver_name: str | None = None
    receiver_phone: str | None = None
    receiver_address: str | None = None
    items: list[OrderItemOut]


class AdminOrderOut(OrderOut):
    """后台订单：补充下单用户信息。"""

    user_id: int
    username: str = ""


class AdminOrderPage(BaseModel):
    """后台订单分页结果。"""

    items: list[AdminOrderOut]
    total: int
    page: int
    size: int

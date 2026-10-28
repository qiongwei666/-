"""行为上报 Schema。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BehaviorCreate(BaseModel):
    """行为上报请求，weight 由后端映射，前端不可伪造。"""

    product_id: int
    behavior_type: Literal["view", "click", "cart", "buy"]


class BehaviorOut(BaseModel):
    """行为记录响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    behavior_type: str
    weight: int
    created_at: datetime

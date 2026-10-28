"""用户行为上报接口。"""

from fastapi import APIRouter

from app.models.behavior import BEHAVIOR_WEIGHTS, UserBehavior
from app.models.product import Product
from app.schemas.behavior import BehaviorCreate, BehaviorOut
from app.schemas.common import ApiResponse
from app.utils.deps import CurrentUser, DbSession
from app.utils.exceptions import BizError
from app.utils.response import success

router = APIRouter(prefix="/behavior", tags=["行为采集"])


@router.post("", response_model=ApiResponse[BehaviorOut], summary="上报用户行为")
def report_behavior(
    payload: BehaviorCreate, current_user: CurrentUser, db: DbSession
) -> dict:
    """记录 view/click/cart/buy 行为，权重完全由后端映射。"""
    if db.get(Product, payload.product_id) is None:
        raise BizError(404, "商品不存在")

    behavior = UserBehavior(
        user_id=current_user.id,
        product_id=payload.product_id,
        behavior_type=payload.behavior_type,
        weight=BEHAVIOR_WEIGHTS[payload.behavior_type],
    )
    db.add(behavior)
    db.commit()
    db.refresh(behavior)
    return success(behavior, "行为已记录")

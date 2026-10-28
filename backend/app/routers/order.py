"""订单接口。"""

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.order import OrderOut
from app.services.order_service import create_order_from_cart, list_orders
from app.utils.deps import CurrentUser, DbSession
from app.utils.response import success

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("", response_model=ApiResponse[OrderOut], summary="从购物车结算")
def create_order(current_user: CurrentUser, db: DbSession) -> dict:
    """模拟支付成功：创建订单、扣库存、加销量、清空购物车、上报 buy 行为。"""
    order = create_order_from_cart(db, current_user)
    return success(order, "下单成功")


@router.get("", response_model=ApiResponse[list[OrderOut]], summary="我的订单")
def my_orders(current_user: CurrentUser, db: DbSession) -> dict:
    """按时间倒序返回当前用户订单。"""
    return success(list_orders(db, current_user.id))

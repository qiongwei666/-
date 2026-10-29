"""订单接口。"""

from fastapi import APIRouter

from app.schemas.admin import ReturnCreate
from app.schemas.common import ApiResponse
from app.schemas.order import OrderOut
from app.services.order_service import (
    confirm_receipt,
    create_order_from_cart,
    list_orders,
    request_return,
)
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


@router.post(
    "/{order_id}/confirm",
    response_model=ApiResponse[OrderOut],
    summary="确认收货",
)
def confirm_order(
    order_id: int, current_user: CurrentUser, db: DbSession
) -> dict:
    """已发货订单确认收货后变为已完成。"""
    order = confirm_receipt(db, current_user.id, order_id)
    return success(order, "已确认收货")


@router.post(
    "/{order_id}/return",
    response_model=ApiResponse[OrderOut],
    summary="申请退货 / 换货",
)
def apply_return(
    order_id: int,
    payload: ReturnCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """对已发货或已完成订单提交退换货申请，等待管理员审批。"""
    order = request_return(db, current_user.id, order_id, payload)
    return success(order, "申请已提交")

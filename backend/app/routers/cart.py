"""购物车接口。"""

from fastapi import APIRouter

from app.schemas.cart import (
    CartAddRequest,
    CartItemOut,
    CartOut,
    CartUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.services.order_service import (
    add_to_cart,
    delete_cart_item,
    get_cart_summary,
    update_cart_item,
)
from app.utils.deps import CurrentUser, DbSession
from app.utils.response import success

router = APIRouter(prefix="/cart", tags=["购物车"])


@router.get("", response_model=ApiResponse[CartOut], summary="我的购物车")
def cart_detail(current_user: CurrentUser, db: DbSession) -> dict:
    """读取当前用户购物车及合计。"""
    return success(get_cart_summary(db, current_user.id))


@router.post("", response_model=ApiResponse[CartItemOut], summary="加入购物车")
def cart_add(payload: CartAddRequest, current_user: CurrentUser, db: DbSession) -> dict:
    """同一商品重复加购时累加数量。"""
    item = add_to_cart(db, current_user.id, payload.product_id, payload.quantity)
    return success(item, "已加入购物车")


@router.put("/{item_id}", response_model=ApiResponse[CartItemOut], summary="修改数量")
def cart_update(
    item_id: int,
    payload: CartUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """修改购物车条目数量。"""
    item = update_cart_item(db, current_user.id, item_id, payload.quantity)
    return success(item, "已更新")


@router.delete("/{item_id}", response_model=ApiResponse[dict], summary="删除购物车条目")
def cart_delete(item_id: int, current_user: CurrentUser, db: DbSession) -> dict:
    """删除当前用户的一条购物车记录。"""
    delete_cart_item(db, current_user.id, item_id)
    return success({"id": item_id}, "已删除")

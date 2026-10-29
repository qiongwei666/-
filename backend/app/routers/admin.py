"""管理后台接口：商品上下架、订单发货与退换货审批。"""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.schemas.admin import (
    AdminProductCreate,
    AdminProductUpdate,
    ProductStatusUpdate,
    ReturnReview,
    ShipRequest,
)
from app.schemas.common import ApiResponse
from app.schemas.order import AdminOrderOut, AdminOrderPage
from app.schemas.product import ProductOut, ProductPage
from app.services import admin_service
from app.utils.deps import DbSession, require_admin
from app.utils.response import success

router = APIRouter(
    prefix="/admin",
    tags=["管理后台"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "/products",
    response_model=ApiResponse[ProductPage],
    summary="后台商品列表",
)
def admin_products(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=50),
    status: Literal["on_sale", "off_sale"] | None = Query(default=None),
) -> dict:
    """包含下架商品，支持关键词与状态筛选。"""
    items, total = admin_service.list_admin_products(db, page, size, keyword, status)
    return success(ProductPage(items=items, total=total, page=page, size=size))


@router.post(
    "/products",
    response_model=ApiResponse[ProductOut],
    summary="新增商品",
)
def create_product(payload: AdminProductCreate, db: DbSession) -> dict:
    """管理员填写商品信息与图片 URL，新增后默认上架。"""
    product = admin_service.create_product(db, payload)
    return success(product, "商品已上架")


@router.put(
    "/products/{product_id}",
    response_model=ApiResponse[ProductOut],
    summary="编辑商品",
)
def update_product(product_id: int, payload: AdminProductUpdate, db: DbSession) -> dict:
    """只更新请求中传入的字段。"""
    product = admin_service.update_product(db, product_id, payload)
    return success(product, "商品已更新")


@router.patch(
    "/products/{product_id}/status",
    response_model=ApiResponse[ProductOut],
    summary="上架 / 下架商品",
)
def update_product_status(
    product_id: int, payload: ProductStatusUpdate, db: DbSession
) -> dict:
    """下架时同步移除购物车中的该商品。"""
    product = admin_service.set_product_status(db, product_id, payload.status)
    message = "商品已上架" if payload.status == "on_sale" else "商品已下架"
    return success(product, message)


@router.get(
    "/orders",
    response_model=ApiResponse[AdminOrderPage],
    summary="后台订单列表",
)
def admin_orders(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None, max_length=20),
) -> dict:
    """查看全部用户订单，按下单时间倒序。"""
    items, total = admin_service.list_admin_orders(db, page, size, status)
    return success(AdminOrderPage(items=items, total=total, page=page, size=size))


@router.post(
    "/orders/{order_id}/ship",
    response_model=ApiResponse[AdminOrderOut],
    summary="订单发货",
)
def ship_order(order_id: int, payload: ShipRequest, db: DbSession) -> dict:
    """已支付订单发货，可填写快递单号。"""
    order = admin_service.ship_order(db, order_id, payload.tracking_no)
    return success(order, "发货成功")


@router.post(
    "/orders/{order_id}/return-review",
    response_model=ApiResponse[AdminOrderOut],
    summary="审批退换货",
)
def review_return(order_id: int, payload: ReturnReview, db: DbSession) -> dict:
    """同意时按用户申请的类型退款或换货；驳回保留申请原因。"""
    order = admin_service.review_return(db, order_id, payload.approve)
    return success(order, "退换货已处理")

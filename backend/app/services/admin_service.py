"""管理后台业务逻辑：商品上下架、订单发货与退换货审批。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.cart import CartItem
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.admin import AdminProductCreate, AdminProductUpdate
from app.utils.exceptions import BizError


def _validate_category(db: Session, category_id: int) -> Category:
    """商品只能挂在已存在的二级分类下。"""
    category = db.get(Category, category_id)
    if category is None:
        raise BizError(404, "分类不存在")
    has_children = db.scalar(
        select(Category.id).where(Category.parent_id == category_id).limit(1)
    )
    if has_children is not None:
        raise BizError(400, "请选择二级分类")
    return category


def _load_admin_order(db: Session, order_id: int) -> Order:
    """按后台订单结构重新加载，避免会话关闭后访问关系。"""
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(
            joinedload(Order.user),
            selectinload(Order.items).joinedload(OrderItem.product),
        )
    )
    if order is None:  # pragma: no cover - 调用前已确认存在
        raise BizError(404, "订单不存在")
    return order


def list_admin_products(
    db: Session,
    page: int,
    size: int,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[list[Product], int]:
    """后台商品列表：包含下架商品，支持关键词与状态筛选。"""
    conditions = []
    if keyword and keyword.strip():
        like_value = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                Product.name.like(like_value),
                Product.description.like(like_value),
            )
        )
    if status:
        conditions.append(Product.status == status)

    total = db.scalar(select(func.count(Product.id)).where(*conditions)) or 0
    stmt = (
        select(Product)
        .where(*conditions)
        .options(joinedload(Product.category))
        .order_by(Product.created_at.desc(), Product.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).unique().all()), total


def create_product(db: Session, payload: AdminProductCreate) -> Product:
    """新增商品，默认上架。"""
    _validate_category(db, payload.category_id)
    product = Product(
        name=payload.name,
        description=payload.description.strip(),
        price=payload.price,
        stock=payload.stock,
        category_id=payload.category_id,
        sales=0,
        image_url=payload.image_url,
        status="on_sale",
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    _ = product.category
    return product


def update_product(
    db: Session, product_id: int, payload: AdminProductUpdate
) -> Product:
    """编辑商品基础信息。"""
    product = db.get(Product, product_id)
    if product is None:
        raise BizError(404, "商品不存在")

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "category_id" in changes:
        _validate_category(db, changes["category_id"])
    if "description" in changes:
        changes["description"] = changes["description"].strip()
    for field, value in changes.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    _ = product.category
    return product


def set_product_status(db: Session, product_id: int, status: str) -> Product:
    """上架 / 下架；下架时同步清理购物车中的该商品。"""
    product = db.get(Product, product_id)
    if product is None:
        raise BizError(404, "商品不存在")

    product.status = status
    if status == "off_sale":
        db.execute(delete(CartItem).where(CartItem.product_id == product_id))
    db.commit()
    db.refresh(product)
    _ = product.category
    return product


def list_admin_orders(
    db: Session,
    page: int,
    size: int,
    status: str | None = None,
) -> tuple[list[Order], int]:
    """后台订单列表，包含下单用户信息。"""
    conditions = []
    if status:
        conditions.append(Order.status == status)

    total = db.scalar(select(func.count(Order.id)).where(*conditions)) or 0
    stmt = (
        select(Order)
        .where(*conditions)
        .options(
            joinedload(Order.user),
            selectinload(Order.items).joinedload(OrderItem.product),
        )
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).unique().all()), total


def ship_order(db: Session, order_id: int, tracking_no: str | None) -> Order:
    """已支付订单发货。"""
    try:
        order = db.scalar(
            select(Order).where(Order.id == order_id).with_for_update()
        )
        if order is None:
            raise BizError(404, "订单不存在")
        if order.status != "paid":
            raise BizError(400, "只有已支付订单可以发货")

        order.status = "shipped"
        order.shipped_at = datetime.now()
        order.tracking_no = tracking_no
        db.commit()
    except BizError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    return _load_admin_order(db, order_id)


def review_return(db: Session, order_id: int, approve: bool) -> Order:
    """管理员审批退换货：同意退款恢复库存，同意换货只改状态。"""
    try:
        order = db.scalar(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
            .options(selectinload(Order.items).joinedload(OrderItem.product))
        )
        if order is None:
            raise BizError(404, "订单不存在")
        if order.status != "return_pending":
            raise BizError(400, "该订单没有待处理的退换货申请")

        if not approve:
            order.status = "return_rejected"
        elif order.return_type == "refund":
            for item in order.items:
                product = db.scalar(
                    select(Product)
                    .where(Product.id == item.product_id)
                    .with_for_update()
                )
                if product is None:
                    continue
                product.stock += item.quantity
                product.sales = max(0, product.sales - item.quantity)
            order.status = "refunded"
        elif order.return_type == "exchange":
            order.status = "exchanged"
        else:
            raise BizError(400, "退换货类型异常")

        db.commit()
    except BizError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    return _load_admin_order(db, order_id)

"""购物车与订单业务逻辑。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.behavior import BEHAVIOR_WEIGHTS, UserBehavior
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.admin import ReturnCreate
from app.utils.exceptions import BizError


def get_cart_items(db: Session, user_id: int) -> list[CartItem]:
    """读取用户购物车，按加入时间排序。"""
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(joinedload(CartItem.product).joinedload(Product.category))
        .order_by(CartItem.id.asc())
    )
    return list(db.scalars(stmt).unique().all())


def get_cart_summary(db: Session, user_id: int) -> dict:
    """组装购物车汇总数据。"""
    items = get_cart_items(db, user_id)
    total_quantity = sum(item.quantity for item in items)
    total_amount = sum((item.product.price * item.quantity for item in items), Decimal("0"))
    return {
        "items": items,
        "total_quantity": total_quantity,
        "total_amount": total_amount,
    }


def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int) -> CartItem:
    """加入购物车；已存在时累加数量。"""
    product = db.get(Product, product_id)
    if product is None:
        raise BizError(404, "商品不存在")
    if product.status != "on_sale":
        raise BizError(400, "商品已下架")
    if product.stock <= 0:
        raise BizError(400, "商品暂时无货")

    item = db.scalar(
        select(CartItem).where(
            CartItem.user_id == user_id, CartItem.product_id == product_id
        )
    )
    target_quantity = quantity + (item.quantity if item else 0)
    if target_quantity > product.stock:
        raise BizError(400, f"库存不足，当前最多可购买 {product.stock} 件")
    if target_quantity > 99:
        raise BizError(400, "单件商品最多购买 99 件")

    if item is None:
        item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.add(item)
    else:
        item.quantity = target_quantity
    db.commit()
    db.refresh(item)
    # 触发关系加载，便于序列化
    _ = item.product
    return item


def get_owned_cart_item(db: Session, user_id: int, item_id: int) -> CartItem:
    """校验购物车条目归属。"""
    item = db.scalar(
        select(CartItem)
        .where(CartItem.id == item_id, CartItem.user_id == user_id)
        .options(joinedload(CartItem.product))
    )
    if item is None:
        raise BizError(404, "购物车条目不存在")
    return item


def update_cart_item(
    db: Session, user_id: int, item_id: int, quantity: int
) -> CartItem:
    """修改购物车数量并校验库存。"""
    item = get_owned_cart_item(db, user_id, item_id)
    if item.product.status != "on_sale":
        raise BizError(400, "商品已下架")
    if quantity > item.product.stock:
        raise BizError(400, f"库存不足，当前最多可购买 {item.product.stock} 件")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    _ = item.product
    return item


def delete_cart_item(db: Session, user_id: int, item_id: int) -> None:
    """删除购物车条目。"""
    item = get_owned_cart_item(db, user_id, item_id)
    db.delete(item)
    db.commit()


def create_order_from_cart(db: Session, user: User) -> Order:
    """从购物车结算：扣库存、加销量、清空购物车并记录 buy 行为。"""
    cart_items = get_cart_items(db, user.id)
    if not cart_items:
        raise BizError(400, "购物车为空，无法下单")

    total_amount = Decimal("0")
    now = datetime.now()
    try:
        order = Order(user_id=user.id, total_amount=Decimal("0"), status="paid", created_at=now)
        db.add(order)
        db.flush()  # 获取订单 ID

        for cart in cart_items:
            # 行锁防止并发超卖；SQLite 会忽略 FOR UPDATE
            product = db.scalar(
                select(Product).where(Product.id == cart.product_id).with_for_update()
            )
            if product is None or product.status != "on_sale":
                raise BizError(400, "购物车中存在已下架商品")
            if cart.quantity > product.stock:
                raise BizError(400, f"商品「{product.name}」库存不足")

            order.items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=cart.quantity,
                    price=product.price,
                )
            )
            product.stock -= cart.quantity
            product.sales += cart.quantity
            total_amount += product.price * cart.quantity

            # 下单行为由后端统一上报，保证权重与数据一致
            db.add(
                UserBehavior(
                    user_id=user.id,
                    product_id=product.id,
                    behavior_type="buy",
                    weight=BEHAVIOR_WEIGHTS["buy"],
                    created_at=now,
                )
            )
            db.delete(cart)

        order.total_amount = total_amount
        db.commit()
    except BizError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    # 重新加载明细，避免会话关闭后访问关系
    order = db.scalar(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
    )
    if order is None:  # pragma: no cover - 理论上提交后一定存在
        raise BizError(500, "订单创建失败")
    return order


def list_orders(db: Session, user_id: int) -> list[Order]:
    """查询用户订单，按时间倒序。"""
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return list(db.scalars(stmt).unique().all())


def _reload_order(db: Session, order_id: int) -> Order:
    """重新加载订单明细，避免序列化时访问已失效的会话关系。"""
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
    )
    if order is None:  # pragma: no cover
        raise BizError(500, "订单加载失败")
    return order


def confirm_receipt(db: Session, user_id: int, order_id: int) -> Order:
    """用户确认收货：已发货 -> 已完成。"""
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .with_for_update()
    )
    if order is None:
        raise BizError(404, "订单不存在")
    if order.status != "shipped":
        raise BizError(400, "只有已发货订单可以确认收货")

    order.status = "completed"
    db.commit()
    return _reload_order(db, order_id)


def request_return(
    db: Session, user_id: int, order_id: int, payload: ReturnCreate
) -> Order:
    """用户对已发货 / 已完成订单申请退货或换货。"""
    order = db.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .with_for_update()
    )
    if order is None:
        raise BizError(404, "订单不存在")
    if order.status not in ("shipped", "completed"):
        raise BizError(400, "只有已发货或已完成的订单可以申请退换货")

    order.status = "return_pending"
    order.return_type = payload.return_type
    order.return_reason = payload.reason
    db.commit()
    return _reload_order(db, order_id)

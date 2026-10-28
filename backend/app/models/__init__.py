"""ORM 模型统一导出，导入本包即可完成元数据注册。"""

from app.models.behavior import BEHAVIOR_WEIGHTS, UserBehavior
from app.models.cart import CartItem
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User

__all__ = [
    "BEHAVIOR_WEIGHTS",
    "CartItem",
    "Category",
    "Order",
    "OrderItem",
    "Product",
    "User",
    "UserBehavior",
]

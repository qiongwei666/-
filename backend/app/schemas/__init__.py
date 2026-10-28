"""Schema 统一导出。"""

from app.schemas.behavior import BehaviorCreate, BehaviorOut
from app.schemas.cart import (
    CartAddRequest,
    CartItemOut,
    CartOut,
    CartUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.schemas.order import OrderItemOut, OrderOut
from app.schemas.product import CategoryOut, ProductOut, ProductPage
from app.schemas.recommend import RecommendResponse
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserOut

__all__ = [
    "ApiResponse",
    "BehaviorCreate",
    "BehaviorOut",
    "CartAddRequest",
    "CartItemOut",
    "CartOut",
    "CartUpdateRequest",
    "CategoryOut",
    "LoginRequest",
    "OrderItemOut",
    "OrderOut",
    "ProductOut",
    "ProductPage",
    "RecommendResponse",
    "RegisterRequest",
    "TokenResponse",
    "UserOut",
]

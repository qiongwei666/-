"""商品接口。"""

from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse
from app.schemas.product import ProductOut, ProductPage
from app.services.product_service import get_product, list_products
from app.utils.deps import DbSession
from app.utils.response import success

router = APIRouter(prefix="/products", tags=["商品"])


@router.get("", response_model=ApiResponse[ProductPage], summary="商品列表")
def products(
    db: DbSession,
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=12, ge=1, le=100, description="每页数量"),
    category_id: int | None = Query(default=None, description="分类 ID，含子分类"),
    keyword: str | None = Query(default=None, max_length=50, description="关键词"),
) -> dict:
    """分页查询商品，默认按销量倒序。"""
    items, total = list_products(db, page, size, category_id, keyword)
    return success(
        ProductPage(items=items, total=total, page=page, size=size)
    )


@router.get("/{product_id}", response_model=ApiResponse[ProductOut], summary="商品详情")
def product_detail(product_id: int, db: DbSession) -> dict:
    """查询单个商品。"""
    return success(get_product(db, product_id))

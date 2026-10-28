"""分类接口。"""

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.product import CategoryOut
from app.services.product_service import get_category_tree
from app.utils.deps import DbSession
from app.utils.response import success

router = APIRouter(tags=["分类"])


@router.get(
    "/categories",
    response_model=ApiResponse[list[CategoryOut]],
    summary="获取分类树",
)
def list_categories(db: DbSession) -> dict:
    """返回一级分类及其子分类。"""
    return success(get_category_tree(db))

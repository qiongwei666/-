"""推荐接口：所有推荐异常内部消化，最差返回热销兜底。"""

from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse
from app.schemas.recommend import RecommendResponse
from app.services.recommend_service import (
    get_home_recommendations,
    get_hot_products,
    get_similar_products,
)
from app.utils.deps import CurrentUser, DbSession
from app.utils.exceptions import BizError
from app.utils.response import success

router = APIRouter(prefix="/recommend", tags=["推荐"])


@router.get("", response_model=ApiResponse[RecommendResponse], summary="首页个性化推荐")
def recommend(
    current_user: CurrentUser,
    db: DbSession,
    scene: str = Query(default="home", description="推荐场景，目前支持 home"),
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=500, description="偏移量，用于滚动加载"),
) -> dict:
    """ALS 个性化结果；无缓存时按行为类目偏好召回，最后热销兜底。"""
    if scene != "home":
        raise BizError(400, "暂不支持的推荐场景")
    items, strategy = get_home_recommendations(
        db, current_user.id, limit, offset
    )
    return success(
        RecommendResponse(items=items, strategy=strategy, scene=scene)
    )


@router.get(
    "/similar/{product_id}",
    response_model=ApiResponse[RecommendResponse],
    summary="相似商品（看了又看）",
)
def similar_products(
    product_id: int,
    db: DbSession,
    limit: int = Query(default=8, ge=1, le=50, description="每批数量"),
    offset: int = Query(default=0, ge=0, le=500, description="偏移量，用于滚动加载"),
) -> dict:
    """ALS + 共访 + 内容相似混合排序，支持 offset 分页，无需登录。"""
    items, strategy = get_similar_products(db, product_id, limit, offset)
    return success(
        RecommendResponse(items=items, strategy=strategy, scene="similar")
    )


@router.get(
    "/hot",
    response_model=ApiResponse[RecommendResponse],
    summary="全局热销榜",
)
def hot_products(
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=500, description="偏移量，用于滚动加载"),
) -> dict:
    """Redis ZSET 热销榜，缓存不可用时查数据库，支持 offset 分页。"""
    items, strategy = get_hot_products(db, limit, offset)
    return success(RecommendResponse(items=items, strategy=strategy, scene="hot"))

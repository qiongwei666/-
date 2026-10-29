"""推荐业务逻辑：ALS + 实时共访 + 内容相似混合排序，Redis 故障自动降级。"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, aliased, joinedload

from app.models.behavior import BEHAVIOR_WEIGHTS, UserBehavior
from app.models.product import Product
from app.redis_client import get_redis
from app.services.product_service import get_product

logger = logging.getLogger(__name__)

HOT_GLOBAL_KEY = "hot:global"
COVIEW_TTL = 60 * 15
COVIEW_WINDOW_DAYS = 45

# Redis 故障熔断：一次连接失败后短时间跳过缓存，避免相似商品接口
# 连续尝试 4 个 Redis key 把响应时间拖到 1 秒以上。
_REDIS_FAIL_UNTIL = 0.0
_REDIS_COOLDOWN_SECONDS = 3.0


def _redis_ready() -> bool:
    """熔断窗口内直接跳过 Redis。"""
    return time.monotonic() >= _REDIS_FAIL_UNTIL


def _mark_redis_failure() -> None:
    """标记 Redis 短暂不可用。"""
    global _REDIS_FAIL_UNTIL
    _REDIS_FAIL_UNTIL = time.monotonic() + _REDIS_COOLDOWN_SECONDS


def _mark_redis_success() -> None:
    """Redis 恢复正常后清除熔断。"""
    global _REDIS_FAIL_UNTIL
    _REDIS_FAIL_UNTIL = 0.0


def _parse_ids(raw: Any) -> list[int]:
    """兼容 JSON 数组、逗号字符串以及 [{product_id: 1}] 结构。"""
    if raw is None:
        return []
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="ignore")
    data: Any = raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = [part for part in raw.split(",") if part.strip()]

    if not isinstance(data, (list, tuple)):
        return []

    result: list[int] = []
    for item in data:
        value: Any = item
        if isinstance(item, dict):
            value = item.get("product_id", item.get("id"))
        try:
            product_id = int(value)
        except (TypeError, ValueError):
            continue
        if product_id > 0 and product_id not in result:
            result.append(product_id)
    return result


def _read_ids(key: str) -> list[int]:
    """安全读取 Redis 中的 ID 列表，任何异常都视为缓存未命中。"""
    if not _redis_ready():
        return []
    try:
        value = _parse_ids(get_redis().get(key))
        _mark_redis_success()
        return value
    except Exception as exc:  # Redis 故障不能影响商城主流程
        _mark_redis_failure()
        logger.warning("读取推荐缓存失败 key=%s: %s", key, exc)
        return []


def _hot_ids_from_cache(limit: int) -> list[int]:
    """读取全局热销 ZSET。"""
    if not _redis_ready():
        return []
    try:
        values = get_redis().zrevrange(HOT_GLOBAL_KEY, 0, max(limit - 1, 0))
        _mark_redis_success()
        return _parse_ids(values)
    except Exception as exc:
        _mark_redis_failure()
        logger.warning("读取热销缓存失败: %s", exc)
        return []


def _hot_ids_from_db(db: Session, limit: int) -> list[int]:
    """数据库兜底热销：按销量倒序，仅上架商品。"""
    stmt = (
        select(Product.id)
        .where(Product.status == "on_sale")
        .order_by(Product.sales.desc(), Product.id.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _fetch_products(db: Session, ids: list[int]) -> list[Product]:
    """按给定 ID 顺序查询商品，自动忽略已删除商品。"""
    unique_ids = list(dict.fromkeys(pid for pid in ids if pid))
    if not unique_ids:
        return []
    stmt = (
        select(Product)
        .where(Product.id.in_(unique_ids), Product.status == "on_sale")
        .options(joinedload(Product.category))
    )
    products = list(db.scalars(stmt).unique().all())
    mapping = {item.id: item for item in products}
    return [mapping[pid] for pid in unique_ids if pid in mapping]


def _hot_products(
    db: Session, limit: int, exclude_ids: set[int] | None = None
) -> list[Product]:
    """获取热销商品，优先 Redis ZSET，失败时查数据库。"""
    exclude_ids = exclude_ids or set()
    ids = _hot_ids_from_cache(limit + len(exclude_ids))
    products = _fetch_products(db, ids)

    # 缓存为空或商品缺失时，用数据库补齐
    if len(products) < limit:
        db_ids = _hot_ids_from_db(db, limit + len(exclude_ids) + 20)
        merged = [item.id for item in products] + db_ids
        products = _fetch_products(db, list(dict.fromkeys(merged)))

    return [item for item in products if item.id not in exclude_ids][:limit]


def _merge(primary: list[Product], extra: list[Product], limit: int) -> list[Product]:
    """按顺序合并去重并截断。"""
    result: list[Product] = []
    seen: set[int] = set()
    for item in [*primary, *extra]:
        if item.id in seen:
            continue
        result.append(item)
        seen.add(item.id)
        if len(result) >= limit:
            break
    return result


def _read_coview_cache(product_id: int) -> list[tuple[int, float, int]]:
    """读取“共同浏览”缓存：[(product_id, score, user_count)]。"""
    if not _redis_ready():
        return []
    try:
        raw = get_redis().get(f"coview:item:{product_id}")
        if not raw:
            _mark_redis_success()
            return []
        data = json.loads(raw)
        result: list[tuple[int, float, int]] = []
        for item in data:
            if isinstance(item, dict):
                pid = int(item.get("product_id"))
                score = float(item.get("score", 0))
                users = int(item.get("users", 0))
            else:
                pid, score, users = int(item[0]), float(item[1]), int(item[2])
            result.append((pid, score, users))
        _mark_redis_success()
        return result
    except Exception as exc:
        _mark_redis_failure()
        logger.debug("读取共访缓存失败 product=%s: %s", product_id, exc)
        return []


def _write_coview_cache(product_id: int, data: list[tuple[int, float, int]]) -> None:
    """写入共访缓存；Redis 异常时静默忽略。"""
    if not _redis_ready():
        return
    try:
        payload = [
            {"product_id": pid, "score": round(score, 4), "users": users}
            for pid, score, users in data
        ]
        get_redis().setex(
            f"coview:item:{product_id}",
            COVIEW_TTL,
            json.dumps(payload, ensure_ascii=False),
        )
        _mark_redis_success()
    except Exception as exc:
        _mark_redis_failure()
        logger.debug("写入共访缓存失败 product=%s: %s", product_id, exc)


def _coview_scores(
    db: Session, product_id: int, limit: int = 40
) -> list[tuple[int, float, int]]:
    """实时共访召回：看过当前商品的用户，还看过哪些商品。

    数据直接来自 user_behavior，因此不需要等下一次 ALS 离线训练，
    对新产生的点击 / 浏览行为也能起到补充作用。
    """
    cached = _read_coview_cache(product_id)
    if cached:
        return cached

    cutoff = datetime.now() - timedelta(days=COVIEW_WINDOW_DAYS)
    current = aliased(UserBehavior)
    other = aliased(UserBehavior)
    weight_expr = case(
        (other.behavior_type == "buy", BEHAVIOR_WEIGHTS["buy"]),
        (other.behavior_type == "cart", BEHAVIOR_WEIGHTS["cart"]),
        (other.behavior_type == "click", BEHAVIOR_WEIGHTS["click"]),
        else_=BEHAVIOR_WEIGHTS["view"],
    )
    score_expr = func.sum(weight_expr).label("score")
    user_count_expr = func.count(func.distinct(current.user_id)).label("users")

    stmt = (
        select(
            other.product_id.label("product_id"),
            score_expr,
            user_count_expr,
        )
        .select_from(current)
        .join(
            other,
            (other.user_id == current.user_id)
            & (other.product_id != current.product_id),
        )
        .where(
            current.product_id == product_id,
            current.created_at >= cutoff,
            other.created_at >= cutoff,
        )
        .group_by(other.product_id)
        .order_by(user_count_expr.desc(), score_expr.desc(), other.product_id.asc())
        .limit(limit)
    )
    try:
        rows = db.execute(stmt).all()
        data = [
            (int(row.product_id), float(row.score), int(row.users))
            for row in rows
        ]
        if data:
            _write_coview_cache(product_id, data)
        return data
    except Exception as exc:
        logger.warning("共访计算失败 product=%s: %s", product_id, exc)
        return []


def _category_products(
    db: Session, category_id: int, product_id: int, limit: int = 40
) -> list[Product]:
    """同分类热销候选，保证新商品也有兜底。"""
    stmt = (
        select(Product)
        .where(
            Product.category_id == category_id,
            Product.id != product_id,
            Product.status == "on_sale",
        )
        .options(joinedload(Product.category))
        .order_by(Product.sales.desc(), Product.id.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt).unique().all())


def _user_interacted_ids(db: Session, user_id: int) -> set[int]:
    """用户已产生过行为的商品 ID，个性化召回时不再重复推荐。"""
    stmt = (
        select(UserBehavior.product_id)
        .where(UserBehavior.user_id == user_id)
        .distinct()
    )
    return set(db.scalars(stmt).all())


def _behavior_candidates(
    db: Session,
    user_id: int,
    limit: int,
    interacted: set[int] | None = None,
) -> list[Product]:
    """按行为类目偏好召回候选。

    Redis 中的 ALS 结果缺失时（未训练、新行为、Redis 故障），用
    view/click/cart/buy 的加权次数统计类目偏好：偏好越高的类目越靠前，
    同类目内按销量排序，并排除用户已有行为的商品。没有行为时返回空列表，
    由全局热销兜底。
    """
    affinity_rows = db.execute(
        select(Product.category_id, func.sum(UserBehavior.weight).label("score"))
        .join(Product, Product.id == UserBehavior.product_id)
        .where(UserBehavior.user_id == user_id)
        .group_by(Product.category_id)
    ).all()
    if not affinity_rows:
        return []

    affinity = {
        int(row.category_id): float(row.score or 0) for row in affinity_rows
    }
    max_score = max(affinity.values()) or 1.0
    if interacted is None:
        interacted = _user_interacted_ids(db, user_id)

    stmt = (
        select(Product)
        .where(Product.status == "on_sale")
        .options(joinedload(Product.category))
    )
    if interacted:
        stmt = stmt.where(Product.id.notin_(interacted))
    products = list(db.scalars(stmt).unique().all())
    products.sort(
        key=lambda item: (
            -affinity.get(item.category_id, 0.0) / max_score,
            -item.sales,
            item.id,
        )
    )
    return products[:limit]


def _build_similar_ranking(
    db: Session,
    product: Product,
    als_ids: list[int],
    content_ids: list[int],
    coview: list[tuple[int, float, int]],
    category_items: list[Product],
    hot_items: list[Product],
) -> tuple[list[Product], str]:
    """把多路召回合并成分数，产生稳定、可分页的相似商品序列。"""
    scores: dict[int, float] = defaultdict(float)

    # 1) ALS 物品相似度：排名越靠前权重越高
    als_count = max(len(als_ids), 1)
    for rank, product_id in enumerate(als_ids):
        scores[product_id] += 0.55 * (1 - rank / als_count) + 0.05

    # 2) 用户共访：真实点击 / 浏览形成的短期关联，归一化后叠加
    if coview:
        max_score = max((score for _, score, _ in coview), default=1.0) or 1.0
        coview_count = max(len(coview), 1)
        for rank, (product_id, score, users) in enumerate(coview):
            normalized = score / max_score
            user_boost = min(users, 10) / 10
            scores[product_id] += (
                0.30 * normalized
                + 0.08 * user_boost
                + 0.06 * (1 - rank / coview_count)
            )

    # 3) 内容相似：新商品冷启动主力
    content_count = max(len(content_ids), 1)
    for rank, product_id in enumerate(content_ids):
        scores[product_id] += 0.20 * (1 - rank / content_count) + 0.02

    # 4) 同分类热销与全局热销兜底
    for rank, item in enumerate(category_items):
        scores[item.id] += 0.08 * (1 - rank / max(len(category_items), 1))
    for rank, item in enumerate(hot_items):
        scores[item.id] += 0.03 * (1 - rank / max(len(hot_items), 1))

    scores.pop(product.id, None)

    # 一次性加载候选商品，保持数据库查询次数固定
    all_ids = [pid for pid in scores if pid != product.id]
    product_mapping = {
        item.id: item for item in _fetch_products(db, all_ids)
    }
    ranked = [
        item
        for item in product_mapping.values()
        if item.id != product.id
    ]
    ranked.sort(
        key=lambda item: (-scores.get(item.id, 0.0), -item.sales, item.id)
    )

    if als_ids and coview:
        strategy = "hybrid"
    elif als_ids:
        strategy = "item_als"
    elif coview:
        strategy = "coview"
    elif content_ids:
        strategy = "content"
    elif category_items:
        strategy = "category"
    else:
        strategy = "hot"
    return ranked, strategy


def get_hot_products(
    db: Session, limit: int = 10, offset: int = 0
) -> tuple[list[Product], str]:
    """全局热销榜，支持 offset 分页。异常时返回数据库热销，绝不上抛。"""
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    try:
        products = _hot_products(db, offset + limit)
        return products[offset : offset + limit], "hot"
    except Exception as exc:
        logger.exception("获取热销商品失败: %s", exc)
        return [], "empty"


def get_home_recommendations(
    db: Session, user_id: int, limit: int = 10, offset: int = 0
) -> tuple[list[Product], str]:
    """首页个性化推荐，支持 offset 分页。

    流程：rec:user:{uid}（ALS）-> 行为类目偏好召回 -> 热销补齐。
    ALS 缓存缺失或 Redis 故障时仍能给出与热销榜不同的个性化结果；
    任何异常最终降级为热销，不会抛给前端。
    """
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    need = offset + limit
    try:
        cached_ids = _read_ids(f"rec:user:{user_id}")
        als_products = _fetch_products(db, cached_ids) if cached_ids else []

        interacted = _user_interacted_ids(db, user_id)
        behavior_products = _behavior_candidates(
            db, user_id, need, interacted=interacted
        )

        products = _merge(als_products, behavior_products, need)
        if len(products) < need:
            exclude = {item.id for item in products}
            if behavior_products:
                # 个性化链路下不把已浏览/购买的商品重新塞回列表
                exclude |= interacted
            products = _merge(products, _hot_products(db, need, exclude), need)

        if not products:
            return [], "empty"
        if als_products:
            strategy = "als"
        elif behavior_products:
            strategy = "behavior"
        else:
            strategy = "hot"
        return products[offset : offset + limit], strategy
    except Exception as exc:
        logger.exception("生成首页推荐失败，降级热销: %s", exc)
        try:
            products = _hot_products(db, need)
            return products[offset : offset + limit], "hot"
        except Exception:
            return [], "empty"


def get_similar_products(
    db: Session, product_id: int, limit: int = 8, offset: int = 0
) -> tuple[list[Product], str]:
    """相似商品信息流：ALS + 共访 + 内容 + 同分类 + 热销混合排序。

    支持 offset 分页，前端滚动到底部时可继续加载下一批相似商品。
    商品不存在时仍返回明确的 404 业务错误；其他异常全部降级，不抛 500。
    """
    limit = max(1, min(limit, 50))
    offset = max(0, offset)
    product = get_product(db, product_id)

    try:
        als_ids = _read_ids(f"sim:item:{product_id}")
        content_ids = _read_ids(f"rec:content:{product_id}")
        coview = _coview_scores(db, product_id)
        category_items = _category_products(
            db, product.category_id, product_id, limit=50
        )
        hot_items = _hot_products(db, 50, exclude_ids={product_id})

        ranked, strategy = _build_similar_ranking(
            db,
            product,
            als_ids,
            content_ids,
            coview,
            category_items,
            hot_items,
        )
        return ranked[offset : offset + limit], strategy
    except Exception as exc:
        logger.exception("相似商品混合排序失败，降级同分类: %s", exc)
        try:
            fallback = _category_products(
                db, product.category_id, product_id, limit=offset + limit
            )
            return fallback[offset : offset + limit], "category"
        except Exception:
            return [], "empty"

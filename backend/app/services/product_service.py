"""商品与分类查询逻辑。"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import CategoryOut
from app.utils.exceptions import BizError


def get_category_tree(db: Session) -> list[CategoryOut]:
    """返回分类树。种子数据为二级结构，这里做了通用递归组装。"""
    categories = list(db.scalars(select(Category).order_by(Category.id)).all())
    nodes: dict[int, CategoryOut] = {
        item.id: CategoryOut(
            id=item.id, name=item.name, parent_id=item.parent_id, children=[]
        )
        for item in categories
    }
    roots: list[CategoryOut] = []
    for item in categories:
        node = nodes[item.id]
        parent = nodes.get(item.parent_id) if item.parent_id else None
        if parent is None:
            roots.append(node)
        else:
            parent.children.append(node)
    return roots


def get_descendant_category_ids(db: Session, category_id: int) -> list[int]:
    """取得分类自身及全部后代 ID，支持按一级分类筛选商品。"""
    rows = db.execute(select(Category.id, Category.parent_id)).all()
    children_map: dict[int, list[int]] = {}
    known: set[int] = set()
    for cid, parent_id in rows:
        known.add(cid)
        if parent_id is not None:
            children_map.setdefault(parent_id, []).append(cid)

    if category_id not in known:
        raise BizError(404, "分类不存在")

    result: list[int] = []
    stack = [category_id]
    while stack:
        current = stack.pop()
        result.append(current)
        stack.extend(children_map.get(current, []))
    return result


def list_products(
    db: Session,
    page: int,
    size: int,
    category_id: int | None = None,
    keyword: str | None = None,
) -> tuple[list[Product], int]:
    """分页查询商品，支持分类（含子分类）与关键词，仅返回上架商品。"""
    conditions = [Product.status == "on_sale"]
    if category_id is not None:
        category_ids = get_descendant_category_ids(db, category_id)
        conditions.append(Product.category_id.in_(category_ids))
    if keyword and keyword.strip():
        like_value = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                Product.name.like(like_value),
                Product.description.like(like_value),
            )
        )

    total = db.scalar(
        select(func.count(Product.id)).where(*conditions)
    ) or 0
    stmt = (
        select(Product)
        .where(*conditions)
        .options(joinedload(Product.category))
        .order_by(Product.sales.desc(), Product.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.scalars(stmt).unique().all())
    return items, total


def get_product(db: Session, product_id: int) -> Product:
    """按 ID 查询商品，不存在时抛业务异常。"""
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id, Product.status == "on_sale")
        .options(joinedload(Product.category))
    )
    if product is None:
        raise BizError(404, "商品不存在")
    return product

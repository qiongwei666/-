"""后端 API 集成测试。

使用独立 SQLite 文件 + 不可用 Redis 端口，验证主流程和推荐降级逻辑。
运行：cd backend && pytest -q
"""

from __future__ import annotations

import os
import tempfile
from decimal import Decimal
from pathlib import Path

# 必须在导入 app 之前设置，确保配置使用测试数据库
TEST_DB = Path(tempfile.gettempdir()) / "ecommerce_rec_pytest.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}?check_same_thread=false"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6399/15"
os.environ["SECRET_KEY"] = "pytest-secret"
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.behavior import UserBehavior
from app.models.category import Category
from app.models.product import Product
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    """启动应用并准备分类 / 商品测试数据。"""
    if TEST_DB.exists():
        TEST_DB.unlink()
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        db = SessionLocal()
        try:
            category = Category(name="测试数码")
            db.add(category)
            db.flush()
            for index in range(4):
                db.add(
                    Product(
                        name=f"测试商品 {index + 1}",
                        description=f"用于接口测试的商品描述 {index + 1}",
                        price=Decimal("99.90") + index,
                        stock=20,
                        category_id=category.id,
                        sales=10 - index,
                        image_url="",
                    )
                )
            db.commit()
        finally:
            db.close()
        yield test_client
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture(scope="module")
def auth(client: TestClient):
    """注册并登录测试用户，返回请求头与商品 ID。"""
    register = client.post(
        "/api/auth/register",
        json={
            "username": "pytest_user",
            "password": "123456",
            "email": "pytest@example.com",
        },
    )
    assert register.status_code == 200
    assert register.json()["code"] == 0, register.text

    login = client.post(
        "/api/auth/login",
        json={"username": "pytest_user", "password": "123456"},
    )
    body = login.json()
    assert body["code"] == 0, body
    token = body["data"]["token"]

    products = client.get("/api/products").json()["data"]["items"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "products": products,
        "user": body["data"]["user"],
    }


def test_unified_response_and_validation(client: TestClient):
    """参数错误也返回 HTTP 200 + 业务错误码。"""
    response = client.post("/api/auth/register", json={"username": "x"})
    assert response.status_code == 200
    assert response.json()["code"] == 422


def test_auth_me_and_unauthorized(client: TestClient, auth):
    """JWT 鉴权：带 Token 成功，不带 Token 返回 401 业务码。"""
    me = client.get("/api/auth/me", headers=auth["headers"]).json()
    assert me["code"] == 0
    assert me["data"]["username"] == "pytest_user"

    unauthorized = client.get("/api/cart")
    assert unauthorized.status_code == 200
    assert unauthorized.json()["code"] == 401


def test_categories_and_products(client: TestClient, auth):
    """分类树、商品列表、详情接口。"""
    categories = client.get("/api/categories").json()
    assert categories["code"] == 0
    assert len(categories["data"]) == 1
    category_id = categories["data"][0]["id"]

    listing = client.get(
        "/api/products", params={"page": 1, "size": 2, "category_id": category_id}
    ).json()
    assert listing["code"] == 0
    assert listing["data"]["total"] == 4
    assert len(listing["data"]["items"]) == 2

    product_id = auth["products"][0]["id"]
    detail = client.get(f"/api/products/{product_id}").json()
    assert detail["code"] == 0
    assert detail["data"]["category_name"] == "测试数码"


def test_cart_order_behavior_and_recommend(client: TestClient, auth):
    """完整走通加购、修改、下单、订单、行为与推荐降级。"""
    headers = auth["headers"]
    products = auth["products"]
    product = products[0]

    # 加入购物车并累加
    added = client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 2},
        headers=headers,
    ).json()
    assert added["code"] == 0
    item_id = added["data"]["id"]

    added_again = client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 1},
        headers=headers,
    ).json()
    assert added_again["data"]["quantity"] == 3

    updated = client.put(
        f"/api/cart/{item_id}", json={"quantity": 2}, headers=headers
    ).json()
    assert updated["code"] == 0
    assert updated["data"]["quantity"] == 2

    cart = client.get("/api/cart", headers=headers).json()["data"]
    assert cart["total_quantity"] == 2
    assert cart["total_amount"] == pytest.approx(199.8, rel=1e-4)

    # 行为上报：weight 由后端映射
    view = client.post(
        "/api/behavior",
        json={"product_id": product["id"], "behavior_type": "view"},
        headers=headers,
    ).json()
    assert view["code"] == 0 and view["data"]["weight"] == 1

    cart_behavior = client.post(
        "/api/behavior",
        json={"product_id": product["id"], "behavior_type": "cart"},
        headers=headers,
    ).json()
    assert cart_behavior["data"]["weight"] == 3

    bad_behavior = client.post(
        "/api/behavior",
        json={"product_id": product["id"], "behavior_type": "share"},
        headers=headers,
    ).json()
    assert bad_behavior["code"] == 422

    # 下单
    order = client.post("/api/orders", headers=headers).json()
    assert order["code"] == 0, order
    assert order["data"]["total_amount"] == pytest.approx(199.8, rel=1e-4)
    assert order["data"]["items"][0]["quantity"] == 2

    empty_cart = client.get("/api/cart", headers=headers).json()["data"]
    assert empty_cart["items"] == []
    assert empty_cart["total_amount"] == 0

    orders = client.get("/api/orders", headers=headers).json()
    assert orders["code"] == 0
    assert len(orders["data"]) == 1

    # 校验库存、销量、buy 行为
    db = SessionLocal()
    try:
        stored_product = db.get(Product, product["id"])
        assert stored_product is not None
        assert stored_product.stock == 18
        assert stored_product.sales == 12

        behaviors = db.query(UserBehavior).all()
        assert len(behaviors) == 3
        buy = [row for row in behaviors if row.behavior_type == "buy"]
        assert len(buy) == 1 and buy[0].weight == 5

        user = db.query(User).filter(User.username == "pytest_user").one()
        assert user.email == "pytest@example.com"
    finally:
        db.close()

    # Redis 不可用：推荐应返回热销兜底，而不是报错
    home = client.get("/api/recommend", headers=headers).json()
    assert home["code"] == 0
    assert home["data"]["strategy"] == "hot"
    assert len(home["data"]["items"]) >= 1

    hot = client.get("/api/recommend/hot").json()
    assert hot["code"] == 0
    assert hot["data"]["items"][0]["id"] == max(
        products, key=lambda item: item["sales"]
    )["id"]

    similar = client.get(
        f"/api/recommend/similar/{product['id']}", params={"limit": 3}
    ).json()
    assert similar["code"] == 0
    assert len(similar["data"]["items"]) >= 1
    assert all(
        item["id"] != product["id"] for item in similar["data"]["items"]
    )

    # 滚动分页：offset 应返回后续且不重复的商品
    first_page = client.get(
        f"/api/recommend/similar/{product['id']}",
        params={"limit": 2, "offset": 0},
    ).json()["data"]["items"]
    second_page = client.get(
        f"/api/recommend/similar/{product['id']}",
        params={"limit": 2, "offset": 2},
    ).json()["data"]["items"]
    first_ids = {item["id"] for item in first_page}
    second_ids = {item["id"] for item in second_page}
    assert not first_ids & second_ids


def test_not_found_business_error(client: TestClient):
    """不存在的商品返回 code=404 而非 HTTP 500。"""
    response = client.get("/api/products/999999")
    assert response.status_code == 200
    assert response.json()["code"] == 404
    assert response.json()["data"] is None

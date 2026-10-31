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

    # Redis 不可用：按行为类目偏好实时召回，而不是报错
    home = client.get("/api/recommend", headers=headers).json()
    assert home["code"] == 0
    assert home["data"]["strategy"] == "behavior"
    assert len(home["data"]["items"]) >= 1
    assert all(item["id"] != product["id"] for item in home["data"]["items"])

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

    # 首页个性化推荐同样支持滚动分页
    home_first = client.get(
        "/api/recommend", headers=headers, params={"limit": 2, "offset": 0}
    ).json()["data"]["items"]
    home_second = client.get(
        "/api/recommend", headers=headers, params={"limit": 2, "offset": 2}
    ).json()["data"]["items"]
    assert not {item["id"] for item in home_first} & {
        item["id"] for item in home_second
    }


def test_not_found_business_error(client: TestClient):
    """不存在的商品返回 code=404 而非 HTTP 500。"""
    response = client.get("/api/products/999999")
    assert response.status_code == 200
    assert response.json()["code"] == 404
    assert response.json()["data"] is None


@pytest.fixture(scope="module")
def admin(client: TestClient):
    """注册测试管理员并把角色提升为 admin，返回鉴权信息。"""
    register = client.post(
        "/api/auth/register",
        json={
            "username": "pytest_admin",
            "password": "123456",
            "email": "pytest_admin@example.com",
        },
    )
    assert register.json()["code"] == 0, register.text

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "pytest_admin").one()
        user.role = "admin"
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/api/auth/login",
        json={"username": "pytest_admin", "password": "123456"},
    ).json()
    assert login["code"] == 0, login
    assert login["data"]["user"]["role"] == "admin"

    categories = client.get("/api/categories").json()["data"]
    return {
        "headers": {"Authorization": f"Bearer {login['data']['token']}"},
        "category_id": categories[0]["id"],
    }


def _create_product(client: TestClient, admin, name: str, stock: int, price: float):
    """通过管理员接口新建测试商品。"""
    response = client.post(
        "/api/admin/products",
        json={
            "name": name,
            "description": "管理员后台新增的测试商品",
            "price": price,
            "stock": stock,
            "category_id": admin["category_id"],
            "image_url": "https://example.com/test-product.jpg",
        },
        headers=admin["headers"],
    ).json()
    assert response["code"] == 0, response
    return response["data"]


def test_admin_permission_guard(client: TestClient, auth, admin):
    """普通用户与匿名请求都不能访问后台接口。"""
    forbidden = client.get("/api/admin/products", headers=auth["headers"]).json()
    assert forbidden["code"] == 403

    unauthorized = client.get("/api/admin/products").json()
    assert unauthorized["code"] == 401

    ship_forbidden = client.post(
        "/api/admin/orders/1/ship",
        json={"tracking_no": None},
        headers=auth["headers"],
    ).json()
    assert ship_forbidden["code"] == 403

    allowed = client.get("/api/admin/orders", headers=admin["headers"]).json()
    assert allowed["code"] == 0


def test_admin_product_create_edit_and_delist(
    client: TestClient, auth, admin
):
    """新增 / 编辑 / 下架商品：前台隐藏，后台仍可见。"""
    product = _create_product(client, admin, "管理员新增商品", 5, 199.9)
    assert product["status"] == "on_sale"

    detail = client.get(f"/api/products/{product['id']}").json()
    assert detail["code"] == 0

    updated = client.put(
        f"/api/admin/products/{product['id']}",
        json={"price": 188.8, "stock": 8},
        headers=admin["headers"],
    ).json()
    assert updated["code"] == 0, updated
    assert updated["data"]["price"] == pytest.approx(188.8)
    assert updated["data"]["stock"] == 8

    off_sale = client.patch(
        f"/api/admin/products/{product['id']}/status",
        json={"status": "off_sale"},
        headers=admin["headers"],
    ).json()
    assert off_sale["code"] == 0
    assert off_sale["data"]["status"] == "off_sale"

    public_list = client.get(
        "/api/products", params={"keyword": "管理员新增商品"}
    ).json()["data"]
    assert public_list["total"] == 0
    assert client.get(f"/api/products/{product['id']}").json()["code"] == 404

    blocked = client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 1},
        headers=auth["headers"],
    ).json()
    assert blocked["code"] == 400
    assert "下架" in blocked["message"]

    admin_list = client.get(
        "/api/admin/products",
        params={"keyword": "管理员新增商品"},
        headers=admin["headers"],
    ).json()["data"]
    assert admin_list["total"] == 1
    assert admin_list["items"][0]["status"] == "off_sale"


def test_admin_ship_and_refund_restores_stock(client: TestClient, auth, admin):
    """发货 -> 确认收货 -> 退款审批：恢复库存与销量，且不能重复审批。"""
    product = _create_product(client, admin, "退款流程商品", 10, 50)
    headers = auth["headers"]

    added = client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 2},
        headers=headers,
    ).json()
    assert added["code"] == 0, added

    order = client.post("/api/orders", headers=headers).json()
    assert order["code"] == 0, order
    order_id = order["data"]["id"]
    assert order["data"]["status"] == "paid"

    shipped = client.post(
        f"/api/admin/orders/{order_id}/ship",
        json={"tracking_no": "SF1234567890"},
        headers=admin["headers"],
    ).json()
    assert shipped["code"] == 0, shipped
    assert shipped["data"]["status"] == "shipped"
    assert shipped["data"]["tracking_no"] == "SF1234567890"

    confirmed = client.post(
        f"/api/orders/{order_id}/confirm", headers=headers
    ).json()
    assert confirmed["code"] == 0, confirmed
    assert confirmed["data"]["status"] == "completed"

    requested = client.post(
        f"/api/orders/{order_id}/return",
        json={"return_type": "refund", "reason": "商品与描述不符"},
        headers=headers,
    ).json()
    assert requested["code"] == 0, requested
    assert requested["data"]["status"] == "return_pending"
    assert requested["data"]["return_type"] == "refund"

    refunded = client.post(
        f"/api/admin/orders/{order_id}/return-review",
        json={"approve": True},
        headers=admin["headers"],
    ).json()
    assert refunded["code"] == 0, refunded
    assert refunded["data"]["status"] == "refunded"

    db = SessionLocal()
    try:
        stored = db.get(Product, product["id"])
        assert stored.stock == 10
        assert stored.sales == 0
    finally:
        db.close()

    repeated = client.post(
        f"/api/admin/orders/{order_id}/return-review",
        json={"approve": True},
        headers=admin["headers"],
    ).json()
    assert repeated["code"] == 400


def test_admin_reject_return_keeps_stock(client: TestClient, auth, admin):
    """驳回换货申请：状态变为已驳回，库存不变。"""
    product = _create_product(client, admin, "换货流程商品", 5, 30)
    headers = auth["headers"]

    client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 1},
        headers=headers,
    )
    order = client.post("/api/orders", headers=headers).json()
    order_id = order["data"]["id"]

    client.post(
        f"/api/admin/orders/{order_id}/ship",
        json={"tracking_no": None},
        headers=admin["headers"],
    )
    requested = client.post(
        f"/api/orders/{order_id}/return",
        json={"return_type": "exchange", "reason": "尺码不合适"},
        headers=headers,
    ).json()
    assert requested["code"] == 0
    assert requested["data"]["return_type"] == "exchange"

    rejected = client.post(
        f"/api/admin/orders/{order_id}/return-review",
        json={"approve": False},
        headers=admin["headers"],
    ).json()
    assert rejected["code"] == 0, rejected
    assert rejected["data"]["status"] == "return_rejected"

    db = SessionLocal()
    try:
        stored = db.get(Product, product["id"])
        assert stored.stock == 4
    finally:
        db.close()


def _register_and_login(client: TestClient, username: str) -> dict:
    """注册并登录独立测试用户，返回鉴权请求头。"""
    register = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "123456",
            "email": f"{username}@example.com",
        },
    )
    assert register.json()["code"] == 0, register.text

    login = client.post(
        "/api/auth/login",
        json={"username": username, "password": "123456"},
    ).json()
    assert login["code"] == 0, login
    return {"Authorization": f"Bearer {login['data']['token']}"}


@pytest.fixture(scope="module")
def address_auth(client: TestClient) -> dict:
    """收货地址流程测试用户。"""
    return _register_and_login(client, "pytest_address")


@pytest.fixture(scope="module")
def other_auth(client: TestClient) -> dict:
    """用于验证跨用户越权的另一个用户。"""
    return _register_and_login(client, "pytest_address_other")


def test_address_crud_and_default(client: TestClient, address_auth):
    """首条自动默认、默认互斥、编辑与删除后默认提升。"""
    headers = address_auth

    empty = client.get("/api/addresses", headers=headers).json()
    assert empty["code"] == 0
    assert empty["data"] == []

    first = client.post(
        "/api/addresses",
        json={
            "receiver_name": "张三",
            "phone": "13800001111",
            "address": "北京市海淀区中关村大街 1 号",
        },
        headers=headers,
    ).json()
    assert first["code"] == 0, first
    assert first["data"]["is_default"] is True
    first_id = first["data"]["id"]

    second = client.post(
        "/api/addresses",
        json={
            "receiver_name": "李四",
            "phone": "13900002222",
            "address": "上海市浦东新区世纪大道 100 号",
        },
        headers=headers,
    ).json()
    assert second["code"] == 0, second
    assert second["data"]["is_default"] is False
    second_id = second["data"]["id"]

    listing = client.get("/api/addresses", headers=headers).json()["data"]
    assert [item["id"] for item in listing] == [first_id, second_id]
    assert sum(1 for item in listing if item["is_default"]) == 1

    switched = client.put(
        f"/api/addresses/{second_id}",
        json={"is_default": True},
        headers=headers,
    ).json()
    assert switched["code"] == 0
    assert switched["data"]["is_default"] is True

    listing = client.get("/api/addresses", headers=headers).json()["data"]
    assert [item["id"] for item in listing][0] == second_id
    defaults = [item["id"] for item in listing if item["is_default"]]
    assert defaults == [second_id]

    edited = client.put(
        f"/api/addresses/{first_id}",
        json={"receiver_name": "张三丰"},
        headers=headers,
    ).json()
    assert edited["code"] == 0
    assert edited["data"]["receiver_name"] == "张三丰"
    assert edited["data"]["address"] == "北京市海淀区中关村大街 1 号"

    removed = client.delete(f"/api/addresses/{second_id}", headers=headers).json()
    assert removed["code"] == 0

    remained = client.get("/api/addresses", headers=headers).json()["data"]
    assert len(remained) == 1
    assert remained[0]["id"] == first_id
    assert remained[0]["is_default"] is True

    bad_phone = client.post(
        "/api/addresses",
        json={
            "receiver_name": "王五",
            "phone": "abc",
            "address": "广州市天河区体育西路 8 号",
        },
        headers=headers,
    ).json()
    assert bad_phone["code"] == 422

    blank_address = client.post(
        "/api/addresses",
        json={
            "receiver_name": "王五",
            "phone": "13700003333",
            "address": "     ",
        },
        headers=headers,
    ).json()
    assert blank_address["code"] == 422


def test_address_ownership_and_order_guard(
    client: TestClient, address_auth, other_auth, admin
):
    """他人地址不可见、不可改；用他人地址下单失败且不改动库存与购物车。"""
    owned = client.post(
        "/api/addresses",
        json={
            "receiver_name": "归属测试",
            "phone": "13600004444",
            "address": "杭州市西湖区文三路 90 号",
        },
        headers=address_auth,
    ).json()["data"]

    other_list = client.get("/api/addresses", headers=other_auth).json()["data"]
    assert other_list == []

    updated = client.put(
        f"/api/addresses/{owned['id']}",
        json={"receiver_name": "越权修改"},
        headers=other_auth,
    ).json()
    assert updated["code"] == 404

    deleted = client.delete(
        f"/api/addresses/{owned['id']}", headers=other_auth
    ).json()
    assert deleted["code"] == 404

    product = _create_product(client, admin, "地址越权商品", 5, 20)
    added = client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 1},
        headers=other_auth,
    ).json()
    assert added["code"] == 0

    blocked = client.post(
        "/api/orders",
        json={"address_id": owned["id"]},
        headers=other_auth,
    ).json()
    assert blocked["code"] == 404

    cart = client.get("/api/cart", headers=other_auth).json()["data"]
    assert cart["total_quantity"] == 1

    db = SessionLocal()
    try:
        stored = db.get(Product, product["id"])
        assert stored.stock == 5
        assert stored.sales == 0
    finally:
        db.close()


def test_order_keeps_address_snapshot(client: TestClient, address_auth, admin):
    """下单保存地址快照；之后编辑或删除地址都不影响历史订单。"""
    snapshot = client.post(
        "/api/addresses",
        json={
            "receiver_name": "快照收货人",
            "phone": "13500005555",
            "address": "南京市鼓楼区中山路 18 号",
        },
        headers=address_auth,
    ).json()["data"]

    product = _create_product(client, admin, "地址快照商品", 5, 25)
    added = client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 2},
        headers=address_auth,
    ).json()
    assert added["code"] == 0

    order = client.post(
        "/api/orders",
        json={"address_id": snapshot["id"]},
        headers=address_auth,
    ).json()
    assert order["code"] == 0, order
    order_id = order["data"]["id"]
    assert order["data"]["receiver_name"] == "快照收货人"
    assert order["data"]["receiver_phone"] == "13500005555"
    assert order["data"]["receiver_address"] == "南京市鼓楼区中山路 18 号"

    client.put(
        f"/api/addresses/{snapshot['id']}",
        json={
            "receiver_name": "已修改收货人",
            "address": "苏州市工业园区星湖街 328 号",
        },
        headers=address_auth,
    )
    client.delete(f"/api/addresses/{snapshot['id']}", headers=address_auth)

    orders = client.get("/api/orders", headers=address_auth).json()["data"]
    kept = next(item for item in orders if item["id"] == order_id)
    assert kept["receiver_name"] == "快照收货人"
    assert kept["receiver_phone"] == "13500005555"
    assert kept["receiver_address"] == "南京市鼓楼区中山路 18 号"

    # 无请求体 / 空对象仍可下单，地址快照为空
    client.post(
        "/api/cart",
        json={"product_id": product["id"], "quantity": 1},
        headers=address_auth,
    )
    plain = client.post("/api/orders", json={}, headers=address_auth).json()
    assert plain["code"] == 0, plain
    assert plain["data"]["receiver_name"] is None

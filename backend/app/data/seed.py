"""生成可演示的种子数据。

执行方式（backend 目录）：
    python -m app.data.seed

注意：脚本会清空并重建业务表，请勿在生产数据库执行。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

from app.data.product_images import IMAGES
from app.database import Base, SessionLocal, engine, ensure_database
from app.models.address import Address
from app.models.behavior import BEHAVIOR_WEIGHTS, UserBehavior
from app.models.cart import CartItem
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.utils.security import hash_password

RANDOM_SEED = 20241001
TARGET_USERS = 300
BEHAVIOR_RANGE = (60, 90)
# 每个商品名词最多两张图，对应两个款式；单图名词只生成一件商品
PRODUCT_VARIANTS = ("经典款", "升级款")

# 一级分类 -> [(子分类, 商品名词), ...]
# 每个名词只归属一个精确子分类，避免商品混挂
CATEGORY_BLUEPRINTS: list[tuple[str, list[tuple[str, list[str]]]]] = [
    (
        "手机数码",
        [
            ("手机", ["5G 智能手机", "轻薄折叠屏手机"]),
            ("耳机音箱", ["降噪蓝牙耳机", "智能音箱"]),
            ("智能穿戴", ["智能运动手表"]),
            ("平板与影像", ["高清平板电脑", "口袋运动相机"]),
            ("数码配件", ["便携充电宝", "无线充电器", "防摔手机壳"]),
        ],
    ),
    (
        "电脑办公",
        [
            ("笔记本", ["轻薄笔记本电脑", "高性能游戏本"]),
            ("台式与显示", ["商务办公台式机", "27 英寸显示器"]),
            ("键鼠外设", ["机械键盘", "无线鼠标"]),
            ("打印与存储", ["激光打印机", "移动固态硬盘"]),
            ("办公配件", ["视频会议摄像头", "人体工学椅"]),
        ],
    ),
    (
        "家用电器",
        [
            ("厨房烹饪", ["多功能电饭煲", "空气炸锅", "破壁料理机", "意式咖啡机"]),
            ("清洁电器", ["扫地机器人", "无线吸尘器"]),
            ("环境电器", ["智能空气净化器"]),
            ("大家电", ["变频空调", "迷你洗衣机"]),
            ("生活小家电", ["电热水壶"]),
        ],
    ),
    (
        "服饰鞋包",
        [
            ("上装", ["纯棉基础 T 恤"]),
            ("外套", ["轻薄羽绒服", "防风冲锋衣"]),
            ("裤装裙装", ["休闲直筒牛仔裤", "法式连衣裙"]),
            ("鞋靴", ["轻便跑步鞋", "真皮通勤皮鞋"]),
            ("箱包配饰", ["大容量双肩包", "复古斜挎包", "羊绒围巾"]),
        ],
    ),
    (
        "美妆个护",
        [
            ("护肤防晒", ["氨基酸洁面乳", "烟酰胺精华液", "保湿面霜", "防晒喷雾"]),
            ("彩妆", ["持妆粉底液", "丝绒口红"]),
            ("洗护发", ["修护洗发水"]),
            ("香氛", ["木质调香水"]),
            ("口腔眼护", ["电动牙刷", "蒸汽眼罩"]),
        ],
    ),
    (
        "食品生鲜",
        [
            ("休闲零食", ["每日坚果礼盒", "手工曲奇饼干", "原切牛肉干", "黑巧克力"]),
            ("冲调饮品", ["云南小粒咖啡", "高山绿茶"]),
            ("米面粮油", ["五常大米", "初榨橄榄油"]),
            ("生鲜水产", ["冷冻虾仁"]),
            ("乳品", ["有机纯牛奶"]),
        ],
    ),
    (
        "运动户外",
        [
            ("健身器材", ["专业瑜伽垫", "可调节哑铃", "竞速跳绳"]),
            ("球类装备", ["碳纤维羽毛球拍"]),
            ("露营装备", ["露营帐篷", "户外折叠椅"]),
            ("户外出行", ["登山背包", "保温运动水壶", "防滑徒步鞋"]),
            ("骑行装备", ["骑行头盔"]),
        ],
    ),
    (
        "图书文娱",
        [
            (
                "图书",
                [
                    "数据分析入门图书",
                    "人工智能通识读本",
                    "经济学经典套装",
                    "儿童绘本套装",
                ],
            ),
            ("文具", ["钢笔礼盒", "手账本套装"]),
            ("乐器", ["入门尤克里里"]),
            ("音频设备", ["便携蓝牙音箱"]),
            ("文创周边", ["桌面护眼台灯", "城市建筑拼图"]),
        ],
    ),
    (
        "母婴玩具",
        [
            ("喂养护理", ["婴儿纸尿裤", "婴幼儿奶粉", "宝宝辅食机"]),
            ("出行安全", ["儿童安全座椅", "儿童平衡车"]),
            ("积木模型", ["益智积木套装", "遥控越野车"]),
            ("益智玩具", ["科学实验套装", "柔软毛绒玩偶"]),
            ("亲子互动", ["亲子桌游"]),
        ],
    ),
    (
        "家居家装",
        [
            ("客厅家具", ["北欧布艺沙发"]),
            ("餐厅家具", ["实木餐桌"]),
            ("卧室软装", ["天然乳胶床垫", "遮光窗帘", "羊毛地毯"]),
            ("灯饰香氛", ["LED 吸顶灯", "香薰蜡烛"]),
            ("卫浴收纳", ["智能门锁", "恒温花洒", "收纳边柜"]),
        ],
    ),
]

# 不同一级分类的价格区间与推荐卖点
CATEGORY_META: dict[str, tuple[float, float, list[str], str]] = {
    "手机数码": (
        299,
        6999,
        ["旗舰芯片", "超长续航", "高清影像", "轻巧便携", "多设备协同"],
        "日常通勤与影音娱乐",
    ),
    "电脑办公": (
        199,
        12999,
        ["高效办公", "沉浸大屏", "静音散热", "高速传输", "人体工学"],
        "学习办公与内容创作",
    ),
    "家用电器": (
        99,
        4999,
        ["智能控制", "节能省电", "低噪运行", "易清洁", "大容量"],
        "家庭日常与品质生活",
    ),
    "服饰鞋包": (
        59,
        899,
        ["亲肤透气", "立体剪裁", "轻量保暖", "百搭耐穿", "大容量收纳"],
        "通勤出街与四季穿搭",
    ),
    "美妆个护": (
        29,
        599,
        ["温和配方", "深层保湿", "持久持妆", "清新香调", "敏感肌友好"],
        "每日护肤与精致妆容",
    ),
    "食品生鲜": (
        19,
        299,
        ["原料新鲜", "低糖健康", "独立包装", "产地直采", "口感醇厚"],
        "家庭囤货与办公室分享",
    ),
    "运动户外": (
        39,
        1999,
        ["专业缓震", "稳固支撑", "轻量便携", "防滑耐磨", "户外防水"],
        "健身训练与周末露营",
    ),
    "图书文娱": (
        29,
        999,
        ["内容系统", "装帧精美", "通俗易懂", "适合入门", "亲子共读"],
        "自我提升与休闲时光",
    ),
    "母婴玩具": (
        39,
        2999,
        ["安全材质", "柔软亲肤", "益智启蒙", "无棱角设计", "易清洗"],
        "宝宝成长与亲子互动",
    ),
    "家居家装": (
        49,
        5999,
        ["环保材质", "简约百搭", "稳固耐用", "舒适支撑", "易打理"],
        "新房布置与居家焕新",
    ),
}

BRAND_POOL = [
    "星耀",
    "云帆",
    "极光",
    "青禾",
    "拾光",
    "远山",
    "简造",
    "澄品",
    "北辰",
    "木棉",
]


def build_products(
    rng: random.Random, roots: list[Category], children: dict[int, list[Category]]
) -> list[Product]:
    """按精确子分类生成商品。

    每个名词的每张图片只生成一件商品，图片全局不重复；
    名词有一张图就生成经典款，有两张图再生成升级款。
    """
    products: list[Product] = []
    now = datetime.now()
    serial = 0
    for root_index, root in enumerate(roots):
        _, sections = CATEGORY_BLUEPRINTS[root_index]
        low, high, features, scene = CATEGORY_META[root.name]
        child_by_name = {child.name: child for child in children[root.id]}

        for sub_name, nouns in sections:
            child = child_by_name[sub_name]
            for noun in nouns:
                base_price = rng.uniform(low, high)
                for variant_index, image_url in enumerate(IMAGES[noun]):
                    brand = BRAND_POOL[(root_index * 3 + serial) % len(BRAND_POOL)]
                    variant = PRODUCT_VARIANTS[
                        variant_index % len(PRODUCT_VARIANTS)
                    ]
                    feature_a = features[serial % len(features)]
                    feature_b = features[(serial + 2) % len(features)]
                    price = Decimal(
                        str(round(base_price * (1 + 0.12 * variant_index), 2))
                    )
                    products.append(
                        Product(
                            name=f"{brand} {noun} {variant}",
                            description=(
                                f"{brand}{noun}{variant}，主打{feature_a}与{feature_b}，"
                                f"面向{scene}。{sub_name}类目优选商品，支持七天无理由退换，"
                                f"提供一年质保与快速发货服务。"
                            ),
                            price=price,
                            stock=rng.randint(80, 500),
                            category_id=child.id,
                            sales=0,
                            image_url=image_url,
                            created_at=now - timedelta(days=rng.randint(10, 120)),
                        )
                    )
                    serial += 1
    return products


def build_order(
    rng: random.Random,
    user: User,
    products: list[Product],
    days_ago: int,
    address: Address | None = None,
) -> Order:
    """为演示用户构造历史订单。"""
    chosen = rng.sample(products, 2)
    order = Order(
        user_id=user.id,
        total_amount=Decimal("0"),
        status="paid",
        created_at=datetime.now() - timedelta(days=days_ago),
        receiver_name=address.receiver_name if address else None,
        receiver_phone=address.phone if address else None,
        receiver_address=address.address if address else None,
    )
    total = Decimal("0")
    for product in chosen:
        quantity = rng.randint(1, 2)
        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=quantity,
                price=product.price,
            )
        )
        total += product.price * quantity
    order.total_amount = total
    return order


def seed() -> None:
    """执行完整数据初始化。"""
    rng = random.Random(RANDOM_SEED)
    started = datetime.now()
    print("[seed] 正在创建数据库与表结构 ...")
    ensure_database()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ---------- 分类 ----------
        roots: list[Category] = []
        subcategories: dict[int, list[Category]] = {}
        for root_name, _ in CATEGORY_BLUEPRINTS:
            roots.append(Category(name=root_name))
        db.add_all(roots)
        db.flush()

        for index, root in enumerate(roots):
            subcategories[root.id] = []
            for sub_name, _ in CATEGORY_BLUEPRINTS[index][1]:
                child = Category(name=sub_name, parent_id=root.id)
                db.add(child)
                subcategories[root.id].append(child)
        db.commit()
        for children in subcategories.values():
            for child in children:
                db.refresh(child)
        print(f"[seed] 分类：{len(roots)} 个一级分类，{sum(len(v) for v in subcategories.values())} 个子分类")

        # ---------- 商品 ----------
        products = build_products(rng, roots, subcategories)
        db.add_all(products)
        db.commit()
        for product in products:
            db.refresh(product)
        child_to_root = {
            child.id: root.id
            for root in roots
            for child in subcategories[root.id]
        }
        products_by_root: dict[int, list[Product]] = {
            root.id: [] for root in roots
        }
        for product in products:
            products_by_root[child_to_root[product.category_id]].append(product)
        print(f"[seed] 商品：{len(products)} 个（图片不重复）")

        # ---------- 用户 ----------
        password_hash = hash_password("123456")
        usernames = ["admin", "demo"] + [
            f"user{i:03d}" for i in range(1, TARGET_USERS - 1)
        ]
        users: list[User] = []
        for username in usernames:
            users.append(
                User(
                    username=username,
                    password_hash=password_hash,
                    email=f"{username}@example.com",
                    role="admin" if username == "admin" else "user",
                    created_at=datetime.now() - timedelta(days=rng.randint(25, 150)),
                )
            )
        db.add_all(users)
        db.commit()
        for user in users:
            db.refresh(user)
        print(f"[seed] 用户：{len(users)} 个（统一密码 123456，含 1 个管理员 admin）")

        # ---------- 行为数据 ----------
        root_ids = [root.id for root in roots]
        behavior_rows: list[dict] = []
        buy_counts: dict[int, int] = {}
        type_pool = ["view", "click", "cart", "buy"]
        type_weights = [0.68, 0.18, 0.08, 0.06]
        now = datetime.now()

        for user in users:
            # demo 用户偏好手机数码 + 电脑办公，便于答辩展示
            if user.username == "demo":
                preferred = root_ids[:2]
            else:
                pref_count = rng.choice([2, 2, 3])
                preferred = rng.sample(root_ids, pref_count)

            count = rng.randint(*BEHAVIOR_RANGE)
            timestamps = sorted(
                now
                - timedelta(
                    days=rng.uniform(1, 85),
                    seconds=rng.randint(0, 86399),
                )
                for _ in range(count)
            )
            for event_time in timestamps:
                if rng.random() < 0.88:
                    root_id = rng.choice(preferred)
                else:
                    root_id = rng.choice(root_ids)
                product = rng.choice(products_by_root[root_id])
                behavior_type = rng.choices(
                    type_pool, weights=type_weights, k=1
                )[0]
                behavior_rows.append(
                    {
                        "user_id": user.id,
                        "product_id": product.id,
                        "behavior_type": behavior_type,
                        "weight": BEHAVIOR_WEIGHTS[behavior_type],
                        "created_at": event_time,
                    }
                )
                if behavior_type == "buy":
                    buy_counts[product.id] = buy_counts.get(product.id, 0) + 1

        db.bulk_insert_mappings(UserBehavior, behavior_rows)
        db.commit()
        print(f"[seed] 行为：{len(behavior_rows)} 条（view/click/cart/buy 权重 1/2/3/5）")

        # 基于行为热度生成商品历史销量，让热销榜与推荐兜底有区分度
        for product in products:
            product.sales = 20 + buy_counts.get(product.id, 0) * 3 + rng.randint(0, 50)
        db.commit()
        print("[seed] 商品销量已根据行为热度回填")

        # ---------- 演示用户收货地址、订单与购物车 ----------
        demo_user = next(user for user in users if user.username == "demo")
        demo_addresses = [
            Address(
                user_id=demo_user.id,
                receiver_name="演示用户",
                phone="13800001234",
                address="北京市海淀区中关村大街 1 号 品寻大厦 8 层 801 室",
                is_default=True,
            ),
            Address(
                user_id=demo_user.id,
                receiver_name="演示用户（公司）",
                phone="13900005678",
                address="上海市浦东新区世纪大道 100 号 环球金融中心 20 层",
                is_default=False,
            ),
        ]
        db.add_all(demo_addresses)
        db.flush()

        demo_products = products_by_root[root_ids[0]] + products_by_root[root_ids[1]]
        db.add(build_order(rng, demo_user, demo_products[:10], 9, demo_addresses[0]))
        db.add(build_order(rng, demo_user, demo_products[10:20], 3, demo_addresses[1]))
        db.add_all(
            [
                CartItem(user_id=demo_user.id, product_id=demo_products[0].id, quantity=1),
                CartItem(user_id=demo_user.id, product_id=demo_products[11].id, quantity=2),
            ]
        )
        db.commit()
        print(
            "[seed] 演示用户 demo 已生成 2 条收货地址、2 笔订单与 2 条购物车记录"
        )

        user_count = db.query(User).count()
        product_count = db.query(Product).count()
        behavior_count = db.query(UserBehavior).count()
        elapsed = (datetime.now() - started).total_seconds()
        print("-" * 56)
        print(
            f"[seed] 完成：用户 {user_count}，商品 {product_count}，行为 {behavior_count}，"
            f"耗时 {elapsed:.2f}s"
        )
        print("[seed] 演示账号：demo / 123456（普通用户）、admin / 123456（管理员）")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

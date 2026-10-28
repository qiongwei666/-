# 品寻 · 基于推荐系统的大数据电商平台

一个前后端分离、带完整推荐闭环的电商平台课程项目。后端使用 **Python 3.13 + FastAPI + SQLAlchemy 2.0 + Pydantic v2**，前端使用 **Vue 3 + Vite + Pinia + Element Plus**，中间件为 **MySQL 8 + Redis 7**，推荐算法使用 **PySpark 4.0 local 模式 ALS**，并配套 **TF-IDF 内容相似度**与**离线评估脚本**。

项目目标不是高并发，而是：**商城主流程完整可跑、推荐链路闭环、架构分层清晰、评估数据可复现**。

---

## 1. 功能一览

- 用户注册、登录、JWT 鉴权、登录态恢复
- 分类树、商品列表、关键词搜索、分类筛选、分页、商品详情
- 购物车增删改查、库存校验、数量与小计
- 从购物车结算下单：扣库存、加销量、清空购物车、记录 `buy` 行为
- 我的订单列表与订单明细
- 用户行为采集：`view / click / cart / buy`，后端映射权重 `1 / 2 / 3 / 5`
- 点击商品卡片上报 `click`，进入详情页上报 `view`
- 首页个性化推荐、商品详情“看了又看”、全局热销榜
- 详情页相似商品采用 **ALS + 实时共访 + TF-IDF + 同分类 + 热销** 混合排序
- 相似商品信息流支持**滚动到底部自动加载下一批**（8 → 16 → 24）
- 推荐多级降级：混合召回 → 内容/同分类 → 全局热销，Redis 故障不影响商城
- Swagger UI 静态资源已本地化，断网也能打开 `/docs` 演示接口
- PySpark ALS 离线训练（隐式反馈）、物品相似度、Redis 热销榜、TF-IDF 冷启动兜底
- 随机 / 热销 / ALS 三组方案的 Precision@10、Recall@10 对比报告

---

## 2. 系统架构

```mermaid
flowchart LR
    B[浏览器<br/>Vue 3 SPA] -->|Axios + JWT<br/>click / view / cart / buy| A[FastAPI<br/>SQLAlchemy 2.0]
    A -->|业务数据 / 行为| M[(MySQL 8)]
    A -->|混合排序 / 共访缓存 / 热销| R[(Redis 7)]
    A -.->|Redis 故障降级| M

    S[PySpark ALS<br/>local[*]] -->|读取 user_behavior| M
    S -->|rec:user / sim:item / hot| R

    C[TF-IDF 内容相似<br/>content_sim.py] -->|rec:content| R
    E[evaluate.py<br/>80/20 时间切分] -->|三组指标| MD[evaluation_result.md]
    E -.->|读取行为| M
```

### 请求链路

1. 前端通过 `/api` 访问后端，Axios 拦截器自动携带 JWT。
2. 后端统一返回 `{ "code": 0, "message": "ok", "data": ... }`，业务错误 HTTP 仍为 200。
3. 点击商品卡片写入 `click`，进入详情页写入 `view`，加购 / 下单写入 `cart / buy`。
4. 离线任务把用户推荐、物品相似度、热销榜写入 Redis。
5. 详情页相似商品实时混合 ALS 物品相似、共访行为、内容相似和热销榜。
6. 首页 / 详情页推荐位异步加载，任意异常自动回退，不阻塞商城页面。

---

## 3. 目录结构

```text
ecommerce-rec/
├── docker-compose.yml          # 仅启动 MySQL 8 + Redis 7
├── README.md
├── .python-version             # 固定 Python 3.13
├── evaluation_result.md        # evaluate.py 自动生成
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI 入口、异常处理、路由注册
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # Engine / Session / 建库建表
│   │   ├── redis_client.py     # 懒加载 Redis 客户端
│   │   ├── models/             # 7 张 ORM 表
│   │   ├── schemas/            # Pydantic v2 Schema
│   │   ├── routers/            # 7 组 API
│   │   ├── services/           # 认证 / 商品 / 订单 / 推荐业务
│   │   ├── utils/              # JWT、bcrypt、依赖、统一响应
│   │   ├── static/swagger-ui/  # 自托管 Swagger UI（离线可用）
│   │   └── data/seed.py        # 300 用户 / 200 商品 / 2.2w+ 行为
│   └── tests/test_api.py       # 主流程 + 降级集成测试
├── recommender/
│   ├── config.py               # 与 backend/.env 共用配置
│   ├── train_als.py            # PySpark ALS 训练
│   ├── content_sim.py          # TF-IDF 内容相似
│   └── evaluate.py             # 三组离线指标
├── frontend/
│   └── src/                    # Vue 3 页面、组件、Pinia、Axios
└── docs/screenshots/           # 答辩截图存放位置
```

---

## 4. 数据设计

### 4.1 MySQL 业务表

| 表 | 关键字段 | 说明 |
| --- | --- | --- |
| `user` | id, username, password_hash, email, created_at | 用户 |
| `category` | id, name, parent_id | 二级分类树 |
| `product` | id, name, description, price, stock, category_id, sales, image_url | 商品 |
| `cart_item` | id, user_id, product_id, quantity | 唯一约束 `(user_id, product_id)` |
| `order` | id, user_id, total_amount, status, created_at | 订单，默认 `paid` |
| `order_item` | id, order_id, product_id, quantity, price | 成交价快照 |
| `user_behavior` | id, user_id, product_id, behavior_type, weight, created_at | 推荐数据源 |

`user_behavior` 建立 `idx_user_time(user_id, created_at)` 与 `idx_product(product_id)` 索引。

### 4.2 Redis 键

| Key | 类型 | 写入方 | 用途 |
| --- | --- | --- | --- |
| `rec:user:{uid}` | string(JSON) | `train_als.py` | 用户 Top20 推荐商品 ID |
| `sim:item:{iid}` | string(JSON) | `train_als.py` | ALS 物品相似 Top10 |
| `rec:content:{iid}` | string(JSON) | `content_sim.py` | 新商品内容相似兜底 |
| `coview:item:{iid}` | string(JSON) | 推荐接口实时计算 | 最近共访商品及权重，TTL 15 分钟 |
| `hot:global` | zset | `train_als.py` | 全局热销榜，score=销量 |
| `hot:category:{cid}` | zset | `train_als.py` | 类目热销榜 |

### 4.3 点击商品后“下滑出现相似商品”的实现

这是本项目最接近淘宝的交互链路：

```text
用户点击商品卡片
  → POST /api/behavior {behavior_type: "click"}
  → 进入详情页 POST /api/behavior {behavior_type: "view"}
  → 详情页加载 GET /api/recommend/similar/{id}?limit=8&offset=0

后端相似商品混合召回：
  ① ALS 物品相似       sim:item:{id}         权重 0.55（按排名衰减）
  ② 实时共访行为       coview:item:{id}      权重 0.30 + 共访人数加成
  ③ TF-IDF 内容相似    rec:content:{id}      权重 0.20
  ④ 同分类热销                            权重 0.08
  ⑤ 全局热销           hot:global            权重 0.03
  → 去重、排除当前商品、加权排序、固定顺序分页

前端滚动到底部（距底部 420px）
  → 自动请求 offset=8
  → 再请求 offset=16
  → 最多展示 24 条，显示“已经到底了”
```

- **为什么不是只靠离线 ALS**：ALS 要等下一次训练才能吸收新行为；`coview` 直接查最近 45 天 `user_behavior`，用 15 分钟短 TTL 缓存“和你看了同一商品的人还看了什么”，比等下一次全量训练更快。
- **新商品冷启动**：没有 `sim:item` / 共访数据时，TF-IDF 内容相似和同分类热销会立即接管。
- **稳定性**：Redis 缓存 15 分钟；Redis 不可用则跳过缓存直接查 MySQL，接口仍返回 `code=0`。
- **防止信息流抖动**：同一商品多次请求的候选顺序固定，`offset` 分页不会重复或漏项。

### 4.4 推荐降级策略

```text
首页个性化：
  rec:user:{uid}
    → 不足 10 条用 hot:global 补齐
    → 无缓存 / Redis 异常 / 新用户 → hot:global
    → Redis 与热销缓存都不可用 → MySQL 按 sales 查询

相似商品信息流：
  ALS + 共访 + 内容 + 同分类 + 热销混合排序
    → 单个数据源缺失时其余来源自动补足
    → Redis 异常 → 共访 / 同分类直接查 MySQL
    → 商品不存在 → code=404；其他异常不抛 500
```

- Redis 连接超时 0.25s、读取超时 0.35s，并带短时间故障熔断，保证推荐接口快速失败。
- 推荐服务内部捕获全部异常，绝不把 500 抛给前端。
- 推荐位在前端独立请求、独立 loading，失败只显示“暂无推荐”。

---

## 5. 快速启动

### 5.0 环境要求

| 组件 | 建议版本 | 说明 |
| --- | --- | --- |
| Python | **3.13** | 后端与推荐模块统一使用 |
| Node.js | 18+ | 前端 |
| Java | **17+** | PySpark 4.0 需要 Java 17+ |
| Docker Desktop | 可选 | 用于一键启动 MySQL / Redis |

先在项目根目录准备环境文件：

```powershell
cd backend
copy .env.example .env
```

`.env` 中的 MySQL 密码默认是 `276367`，与 `docker-compose.yml` 一致。

项目根目录的 `.python-version` 已固定为 **3.13**，后端与推荐模块均使用同一 Python 3.13 解释器。

### 5.1 启动 MySQL 与 Redis（Docker Compose）

```powershell
cd ecommerce-rec
docker compose up -d
docker compose ps
```

> 如果本机 3306 / 6379 已被占用，请先停止本地服务，或修改 `docker-compose.yml` 的端口映射，并同步修改 `backend/.env` 的 `DATABASE_URL` / `REDIS_URL`。
>
> 如果使用本机已有的 MySQL 8 与 Redis，可跳过此步：先创建数据库 `ecommerce`，并确认账号密码写入 `.env` 即可。

### 5.2 启动后端（终端 1）

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version   # 应为 Python 3.13.x
pip install -r requirements.txt
python -m app.data.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger 文档：<http://127.0.0.1:8000/docs>（本地静态资源，离线可用）
- 健康检查：<http://127.0.0.1:8000/api/health>（返回 database / redis / **python_version**）
- seed 会重建业务表并打印：用户 300、商品 200、行为 22295。
- 演示账号：**demo / 123456**（所有种子用户密码均为 `123456`）。

### 5.3 训练推荐模型（终端 2）

```powershell
cd recommender
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version   # 应为 Python 3.13.x
pip install -r requirements.txt

# PySpark 需要 Java 17+；脚本会自动探测，也可按实际安装路径显式设置
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"

python content_sim.py
python train_als.py
python evaluate.py
```

说明：

- `train_als.py` 首次会尝试自动下载 MySQL JDBC 驱动到 `recommender/jars/`；下载失败会自动回退为“PyMySQL 导出 CSV → Spark 读取”，不影响训练。
- 训练完成后 Redis 中应有 `rec:user:*`、`sim:item:*`、`rec:content:*`、`hot:global`、`hot:category:*`。
- `evaluate.py` 会在项目根目录生成 `evaluation_result.md`。
- 当前使用 **Python 3.13 + PySpark 4.0.5 + numpy 2.2.6**；依赖版本均已提供 Python 3.13 预编译 wheel。
- PySpark 首次启动较慢、日志较多，属于正常现象；Windows 下出现 `Did not find winutils.exe` 的 WARN 不影响本项目的 local 模式训练。
- 项目使用 PySpark 4.0.5；该版本已移除弃用的 `ALS.train` 类方法，项目使用等价的 `ALS(rank=10, maxIter=10, regParam=0.01, implicitPrefs=True, alpha=40)` + `fit()`；参数与任务书一致，隐式反馈方案已在 `evaluation_result.md` 中说明。

### 5.4 启动前端（终端 3）

```powershell
cd frontend
npm install
npm run dev
```

打开 <http://127.0.0.1:5173>。

Vite 已将 `/api` 代理到 `http://127.0.0.1:8000`；如需修改，编辑 `vite.config.js` 或设置 `VITE_API_BASE_URL`。

### 5.5 一键检查后端

```powershell
cd backend
pytest -q
```

测试使用独立 SQLite 文件和不可达的 Redis 端口，覆盖注册登录、商品、购物车、下单、行为、推荐热销兜底与 404 业务错误。

---

## 6. 接口清单

统一前缀 `/api`，统一响应 `{code, message, data}`。

| 方法 | 路径 | 认证 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 否 | 注册 |
| POST | `/api/auth/login` | 否 | 登录，返回 JWT |
| GET | `/api/auth/me` | 是 | 当前用户 |
| GET | `/api/categories` | 否 | 分类树 |
| GET | `/api/products` | 否 | 分页 / 分类 / 关键词 |
| GET | `/api/products/{id}` | 否 | 商品详情 |
| GET | `/api/cart` | 是 | 购物车 |
| POST | `/api/cart` | 是 | 加购 |
| PUT | `/api/cart/{id}` | 是 | 改数量 |
| DELETE | `/api/cart/{id}` | 是 | 删除 |
| POST | `/api/orders` | 是 | 从购物车结算 |
| GET | `/api/orders` | 是 | 我的订单 |
| POST | `/api/behavior` | 是 | 上报行为，weight 后端映射 |
| GET | `/api/recommend?scene=home&limit=10` | 是 | 首页个性化推荐 |
| GET | `/api/recommend/similar/{product_id}?limit=8&offset=0` | 否 | 看了又看，支持滚动分页 |
| GET | `/api/recommend/hot?limit=10` | 否 | 全局热销榜 |
| GET | `/api/health` | 否 | 数据库 / Redis 健康检查 |

FastAPI 的完整参数与响应模型见 `/docs`。

---

## 7. 评估结果

完整报告见 [evaluation_result.md](evaluation_result.md)。评估方法：

- 按每个用户行为时间排序，前 80% 训练、后 20% 测试；
- 测试集中出现过的商品作为相关商品；
- 三种方案都过滤训练集中已交互商品；
- 计算平均 Precision@10 与 Recall@10。

| 推荐方案 | Precision@10 | Recall@10 | 命中总数 | 推荐商品覆盖数 |
| --- | ---: | ---: | ---: | ---: |
| 随机推荐（baseline） | 0.0303 | 0.0231 | 91 | 200 |
| 全局热销 | 0.0300 | 0.0228 | 90 | 23 |
| **ALS 协同过滤** | **0.2013** | **0.1534** | **604** | **200** |

ALS 的 Precision@10 约为随机基线的 **6.6 倍**，证明用户-商品隐向量确实学习到了类目偏好，而不是简单复述全局热销。

> 结果由 seed 固定随机种子与 ALS `seed=42` 产生，可重复运行 `python evaluate.py` 复现。

---

## 8. 配置项说明（backend/.env）

| 配置 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | 品寻 · 推荐电商平台 | 应用名称 |
| `APP_ENV` | development | 运行环境 |
| `DEBUG` | true | 调试模式 |
| `SECRET_KEY` | demo secret | JWT 签名密钥，生产必须替换 |
| `ALGORITHM` | HS256 | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 10080 | Token 有效期（7 天） |
| `DATABASE_URL` | `mysql+pymysql://root:276367@127.0.0.1:3306/ecommerce?charset=utf8mb4` | SQLAlchemy 连接串 |
| `DATABASE_ECHO` | false | 是否打印 SQL |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis 连接串 |
| `REDIS_CONNECT_TIMEOUT` | 0.25 | Redis 连接超时（秒） |
| `REDIS_SOCKET_TIMEOUT` | 0.35 | Redis 读超时（秒） |
| `CORS_ORIGINS` | localhost / 127.0.0.1:5173 | 允许跨域的前端地址，逗号分隔 |

---

## 9. 答辩截图位置

截图已由真实运行页面导出到 `docs/screenshots/`，可直接在报告中引用：

| 文件 | 内容 |
| --- | --- |
| `docs/screenshots/home.png` | 首页轮播、热销区、ALS 个性化推荐 |
| `docs/screenshots/product-detail.png` | 商品详情、加购 / 立即购买、看了又看 |
| `docs/screenshots/products.png` | 商品列表、分类树、搜索分页 |
| `docs/screenshots/cart.png` | 购物车与结算摘要 |
| `docs/screenshots/checkout.png` | 确认订单页 |
| `docs/screenshots/orders.png` | 我的订单 |
| `docs/screenshots/mobile-home.png` | 移动端响应式首页 |
| `docs/screenshots/swagger.png` | 自托管 Swagger 接口文档 |
| `docs/screenshots/evaluation.png` | 三组推荐方案指标可视化 |

### 预览

![首页与个性化推荐](docs/screenshots/home.png)

![商品详情与看了又看](docs/screenshots/product-detail.png)

![推荐效果评估](docs/screenshots/evaluation.png)

---

## 10. 已知局限

- 单机 `local[*]` 跑 PySpark，仅用于课程演示，不做分布式集群与高并发压测。
- ALS 将“行为权重求和”作为隐式反馈置信度，未做实时增量训练；新行为由 15 分钟 TTL 的共访缓存提供短期实时补充，长期偏好仍在下次离线训练后生效。
- 推荐结果未做多样性重排、曝光去重和线上 A/B 实验。
- 支付为模拟流程，下单即 `paid`；没有退款、优惠券、库存超卖分布式锁。
- 商品图使用京东 / 苏宁 / 阿里 CDN 外链，网络不可用时会显示前端内置占位图。
- 评估采用离线时间切分，只反映历史数据上的排序效果，不等同于线上收益。

---

## 11. 常见问题

**Q1：MySQL 连接失败 / Access denied？**  
检查 `backend/.env` 的 `DATABASE_URL` 密码是否为 `276367`，以及 MySQL 是否监听 `127.0.0.1:3306`。

**Q2：Redis 没启动，推荐还能用吗？**  
可以。推荐接口会捕获 Redis 异常并降级为数据库热销；这是验收项之一。

**Q3：PySpark 报 Java 版本错误？**  
安装 JDK 17+。`recommender/config.py` 会自动探测 Java 17/21；也可手动设置 `$env:JAVA_HOME` 指向 JDK 根目录。

**Q4：seed 能重复执行吗？**  
可以，但会清空并重建 7 张业务表。不要对重要数据库执行。

**Q5：训练后推荐结果没变化？**  
确认 Redis 与后端使用同一个 `REDIS_URL`，并检查 `redis-cli keys "rec:user:*"` 是否有数据；浏览器刷新后重新进入首页。

---

## 12. 验收自检结果

| # | 验收项 | 结果 |
| --- | --- | --- |
| 1 | MySQL / Redis 可用 | 本机 MySQL 8.0.26 + Redis 5.0.14（兼容 Redis 7 指令）运行正常；`docker-compose.yml` 已通过 YAML 解析与密码一致性检查。当前开发机未安装 Docker Desktop，故运行验证使用本机中间件，Compose 启动方式已写入 README。 |
| 2 | `/docs` 可访问 | 200；Swagger UI 静态资源已本地化，15 个 OpenAPI 路径全部可见。 |
| 3 | seed 数据量 | 用户 300、商品 200、一级分类 10 / 子分类 20、行为 22,295 条；演示过程中会继续累积真实浏览行为。 |
| 4 | 主流程 | 在本机 MySQL 上实测注册 → 登录 → 浏览 → 加购 → 下单 → 订单查询成功，测试后已清理临时用户并恢复库存。 |
| 5 | 行为权重 | 实测 view=1、click=2、cart=3、buy=5；下单由后端自动写入 buy。 |
| 6 | ALS 训练 | Python 3.13.5 + PySpark 4.0.5 下 `train_als.py` 退出码 0；Redis 中 `rec:user:*=300`、`sim:item:*=200`、`hot:global=200`、`hot:category:*=30`。 |
| 7 | 推荐差异 | 演示用户首页策略为 `als`；清空该用户推荐缓存模拟新用户后，策略降级为 `hot`。 |
| 8 | 看了又看 | 策略 `hybrid`（ALS + 真实共访）；首屏 8 条，滚动后 8 → 16 → 24，无重复，末尾显示“已经到底了”。 |
| 9 | 离线评估 | 三组指标齐全，`evaluation_result.md` 自动生成。 |
| 10 | Redis 故障降级 | 指向不可达 Redis 时，首页约 0.28s 返回 `hot`，相似商品约 0.04s 返回 `coview`，始终 `code=0`（已加 3s 熔断，避免连续尝试 Redis）。 |
| 11 | 测试与构建 | Python **3.13.5** 下 `pytest -q`：5 passed；`npm run build`：成功，1714 modules transformed。 |

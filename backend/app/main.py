"""FastAPI 应用入口。"""

import logging
import platform
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import SessionLocal, init_db
from app.redis_client import close_redis, is_redis_available
from app.routers import (
    admin,
    auth,
    behavior,
    cart,
    category,
    order,
    product,
    recommend,
)
from app.utils.exceptions import BizError
from app.utils.response import failure, success

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# 本地静态资源目录（Swagger UI 离线可用，避免答辩现场 CDN 不可访问）
STATIC_DIR = Path(__file__).resolve().parent / "static"
SWAGGER_DIR = STATIC_DIR / "swagger-ui"


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时确保表结构存在，退出时释放 Redis 连接。"""
    init_db()
    logger.info("应用启动完成，Swagger: /docs")
    try:
        yield
    finally:
        close_redis()
        logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "高校综合实践：基于 PySpark ALS 的电商推荐系统。"
        "统一响应格式 `{code, message, data}`，code=0 表示成功。"
    ),
    version="1.0.0",
    lifespan=lifespan,
    # 关闭默认 CDN 文档，改用下方自托管 Swagger UI
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/docs", include_in_schema=False)
def swagger_docs():
    """自托管 Swagger UI，断网也能打开接口文档。"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.APP_NAME} - Swagger UI",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_ui_parameters={"persistAuthorization": True},
    )


@app.get("/docs/oauth2-redirect", include_in_schema=False)
def swagger_oauth2_redirect():
    """Swagger UI OAuth2 回调页（JWT 场景仅用于保持文档兼容）。"""
    return get_swagger_ui_oauth2_redirect_html()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BizError)
async def biz_error_handler(_: Request, exc: BizError) -> JSONResponse:
    """业务异常统一返回 HTTP 200，通过 code 区分。"""
    return JSONResponse(status_code=200, content=failure(exc.code, exc.message))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """参数校验失败也遵循统一响应格式。"""
    errors = exc.errors()
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
        message = f"参数校验失败：{location} {first.get('msg', '')}".strip()
    else:  # pragma: no cover - 极少数情况
        message = "参数校验失败"
    return JSONResponse(status_code=200, content=failure(422, message))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """把框架 HTTP 异常也转换为业务错误码，前端只需处理一种结构。"""
    detail = exc.detail
    message = detail if isinstance(detail, str) else "请求处理失败"
    return JSONResponse(status_code=200, content=failure(exc.status_code, message))


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底异常处理，避免向前端抛裸 500。"""
    logger.exception("未处理异常 %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=200, content=failure(500, "服务器内部错误"))


@app.get("/", tags=["系统"], summary="服务说明")
def root() -> dict:
    """浏览器直接访问时的简易入口。"""
    return success(
        {
            "name": settings.APP_NAME,
            "docs": "/docs",
            "health": "/api/health",
        }
    )


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health() -> dict:
    """检查数据库与 Redis；Redis 故障只标记 degraded。"""
    db_ok = False
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        finally:
            db.close()
    except Exception as exc:
        logger.warning("数据库健康检查失败: %s", exc)

    redis_ok = is_redis_available()
    if db_ok and redis_ok:
        status = "ok"
    elif db_ok:
        status = "degraded"
    else:
        status = "error"
    return success(
        {
            "status": status,
            "database": db_ok,
            "redis": redis_ok,
            "python_version": platform.python_version(),
            "time": datetime.now().isoformat(timespec="seconds"),
        }
    )


# 统一 /api 前缀
app.include_router(auth.router, prefix="/api")
app.include_router(category.router, prefix="/api")
app.include_router(product.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(order.router, prefix="/api")
app.include_router(behavior.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

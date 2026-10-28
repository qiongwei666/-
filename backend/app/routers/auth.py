"""认证接口。"""

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth_service import authenticate_user, register_user
from app.utils.deps import CurrentUser, DbSession
from app.utils.response import success
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[UserOut], summary="用户注册")
def register(payload: RegisterRequest, db: DbSession) -> dict:
    """注册新用户，成功后返回用户信息。"""
    user = register_user(db, payload)
    return success(user, "注册成功")


@router.post("/login", response_model=ApiResponse[TokenResponse], summary="用户登录")
def login(payload: LoginRequest, db: DbSession) -> dict:
    """校验账号密码并签发 JWT。"""
    user = authenticate_user(db, payload)
    token = create_access_token(user.id)
    data = TokenResponse(token=token, user=user)
    return success(data, "登录成功")


@router.get("/me", response_model=ApiResponse[UserOut], summary="获取当前用户")
def me(current_user: CurrentUser) -> dict:
    """前端刷新页面时用于恢复登录态。"""
    return success(current_user)

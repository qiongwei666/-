"""FastAPI 通用依赖：数据库会话、当前登录用户。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.exceptions import BizError
from app.utils.security import decode_token

# auto_error=False：未带 Token 时由我们统一返回业务错误码
bearer_scheme = HTTPBearer(auto_error=False, description="Bearer JWT")

DbSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


def get_current_user(
    credentials: BearerCredentials,
    db: DbSession,
) -> User:
    """从 Authorization 头解析当前用户。"""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise BizError(401, "请先登录")
    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise BizError(401, "登录状态已失效，请重新登录")
    user = db.get(User, user_id)
    if user is None:
        raise BizError(401, "用户不存在或已注销")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    """管理员接口守卫：角色从数据库实时读取。"""
    if current_user.role != "admin":
        raise BizError(403, "需要管理员权限")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]

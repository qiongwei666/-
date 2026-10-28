"""认证业务逻辑。"""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import LoginRequest, RegisterRequest
from app.utils.exceptions import BizError
from app.utils.security import hash_password, verify_password


def register_user(db: Session, payload: RegisterRequest) -> User:
    """注册新用户，用户名与邮箱均需唯一。"""
    exists = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == str(payload.email))
        )
    )
    if exists:
        if exists.username == payload.username:
            raise BizError(400, "用户名已被注册")
        raise BizError(400, "邮箱已被注册")

    user = User(
        username=payload.username,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError(400, "用户名或邮箱已被注册") from None
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    """校验用户名密码，失败统一提示，避免泄露账号是否存在。"""
    user = db.scalar(select(User).where(User.username == payload.username.strip()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise BizError(401, "用户名或密码错误")
    return user

"""用户与认证相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str = Field(min_length=3, max_length=32, description="用户名")
    password: str = Field(min_length=6, max_length=64, description="密码")
    email: EmailStr = Field(description="邮箱")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """去掉首尾空格并禁止空白字符。"""
        value = value.strip()
        if not value or any(ch.isspace() for ch in value):
            raise ValueError("用户名不能包含空格")
        return value


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=64)


class UserOut(BaseModel):
    """返回给前端的用户信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    """登录成功后的令牌与用户信息。"""

    token: str
    token_type: str = "bearer"
    user: UserOut

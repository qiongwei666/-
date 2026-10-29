"""管理后台请求 Schema。"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _clean_text(value: str, field_name: str, max_length: int) -> str:
    """去首尾空格并校验非空。"""
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name}不能为空")
    if len(value) > max_length:
        raise ValueError(f"{field_name}不能超过 {max_length} 个字符")
    return value


def _validate_image_url(value: str) -> str:
    """图片地址支持 http(s) 链接或站内 / 开头路径。"""
    value = value.strip()
    if not value:
        raise ValueError("图片地址不能为空")
    if len(value) > 500:
        raise ValueError("图片地址不能超过 500 个字符")
    if not value.startswith(("http://", "https://", "/")):
        raise ValueError("图片地址需以 http://、https:// 或 / 开头")
    return value


class AdminProductCreate(BaseModel):
    """新增商品。"""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0, le=999999)
    category_id: int = Field(gt=0)
    image_url: str = Field(min_length=1, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _clean_text(value, "商品名称", 120)

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        return _validate_image_url(value)


class AdminProductUpdate(BaseModel):
    """编辑商品，仅更新传入字段。"""

    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0, le=999999)
    category_id: int | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _clean_text(value, "商品名称", 120) if value is not None else None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        return _validate_image_url(value) if value is not None else None


class ProductStatusUpdate(BaseModel):
    """商品上下架。"""

    status: Literal["on_sale", "off_sale"]


class ShipRequest(BaseModel):
    """发货请求，快递单号可选。"""

    tracking_no: str | None = Field(default=None, max_length=64)

    @field_validator("tracking_no")
    @classmethod
    def validate_tracking_no(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ReturnCreate(BaseModel):
    """用户申请退货 / 换货。"""

    return_type: Literal["refund", "exchange"]
    reason: str = Field(min_length=1, max_length=255)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return _clean_text(value, "申请原因", 255)


class ReturnReview(BaseModel):
    """管理员审批退换货。"""

    approve: bool

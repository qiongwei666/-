"""收货地址 Schema。"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = re.compile(r"^[0-9+\-\s]{6,20}$")


def _clean_text(value: str, field_name: str, max_length: int) -> str:
    """去首尾空格并校验非空。"""
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name}不能为空")
    if len(value) > max_length:
        raise ValueError(f"{field_name}不能超过 {max_length} 个字符")
    return value


def _validate_phone(value: str) -> str:
    value = value.strip()
    if not PHONE_PATTERN.fullmatch(value):
        raise ValueError("请输入正确的联系电话")
    return value


class AddressCreate(BaseModel):
    """新增收货地址。"""

    receiver_name: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=6, max_length=20)
    address: str = Field(min_length=5, max_length=255)
    is_default: bool = False

    @field_validator("receiver_name")
    @classmethod
    def validate_receiver_name(cls, value: str) -> str:
        return _clean_text(value, "收货人", 50)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_phone(value)

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        return _clean_text(value, "收货地址", 255)


class AddressUpdate(BaseModel):
    """编辑收货地址，仅更新传入字段。"""

    receiver_name: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    is_default: bool | None = None

    @field_validator("receiver_name")
    @classmethod
    def validate_receiver_name(cls, value: str | None) -> str | None:
        return _clean_text(value, "收货人", 50) if value is not None else None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return _validate_phone(value) if value is not None else None

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str | None) -> str | None:
        return _clean_text(value, "收货地址", 255) if value is not None else None


class AddressOut(BaseModel):
    """收货地址详情。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver_name: str
    phone: str
    address: str
    is_default: bool
    created_at: datetime

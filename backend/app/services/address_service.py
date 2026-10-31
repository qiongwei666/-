"""收货地址业务逻辑。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate
from app.utils.exceptions import BizError


def list_addresses(db: Session, user_id: int) -> list[Address]:
    """默认地址优先，其余按创建时间倒序。"""
    stmt = (
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.desc(), Address.id.desc())
    )
    return list(db.scalars(stmt).all())


def get_owned_address(db: Session, user_id: int, address_id: int) -> Address:
    """校验地址归属，非本人地址按不存在处理。"""
    address = db.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    if address is None:
        raise BizError(404, "收货地址不存在")
    return address


def _lock_user(db: Session, user_id: int) -> None:
    """串行化同一用户的默认地址变更（SQLite 会忽略 FOR UPDATE）。"""
    db.scalar(select(User).where(User.id == user_id).with_for_update())


def _clear_default(db: Session, user_id: int, exclude_id: int | None = None) -> None:
    stmt = select(Address).where(
        Address.user_id == user_id, Address.is_default.is_(True)
    )
    if exclude_id is not None:
        stmt = stmt.where(Address.id != exclude_id)
    for item in db.scalars(stmt).all():
        item.is_default = False


def create_address(db: Session, user_id: int, payload: AddressCreate) -> Address:
    """新增地址；用户没有地址时自动设为默认。"""
    _lock_user(db, user_id)
    has_any = db.scalar(
        select(Address.id).where(Address.user_id == user_id).limit(1)
    )
    is_default = payload.is_default or has_any is None
    if is_default:
        _clear_default(db, user_id)

    address = Address(
        user_id=user_id,
        receiver_name=payload.receiver_name,
        phone=payload.phone,
        address=payload.address,
        is_default=is_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(
    db: Session, user_id: int, address_id: int, payload: AddressUpdate
) -> Address:
    """编辑地址；is_default=True 时取消该用户其他默认地址。"""
    _lock_user(db, user_id)
    address = get_owned_address(db, user_id, address_id)
    data = payload.model_dump(exclude_unset=True)

    if data.pop("is_default", None) is True:
        _clear_default(db, user_id, exclude_id=address.id)
        address.is_default = True

    for field, value in data.items():
        if value is not None:
            setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, user_id: int, address_id: int) -> None:
    """删除地址；删除的是默认地址时，提升最新的一条为默认。"""
    _lock_user(db, user_id)
    address = get_owned_address(db, user_id, address_id)
    was_default = address.is_default

    db.delete(address)
    db.flush()

    if was_default:
        remaining = db.scalar(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.created_at.desc(), Address.id.desc())
            .limit(1)
        )
        if remaining is not None:
            remaining.is_default = True

    db.commit()

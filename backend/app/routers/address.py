"""收货地址接口。"""

from fastapi import APIRouter

from app.schemas.address import AddressCreate, AddressOut, AddressUpdate
from app.schemas.common import ApiResponse
from app.services.address_service import (
    create_address,
    delete_address,
    list_addresses,
    update_address,
)
from app.utils.deps import CurrentUser, DbSession
from app.utils.response import success

router = APIRouter(prefix="/addresses", tags=["收货地址"])


@router.get("", response_model=ApiResponse[list[AddressOut]], summary="我的收货地址")
def address_list(current_user: CurrentUser, db: DbSession) -> dict:
    """默认地址排在最前，其次按创建时间倒序。"""
    return success(list_addresses(db, current_user.id))


@router.post("", response_model=ApiResponse[AddressOut], summary="新增收货地址")
def address_create(
    payload: AddressCreate, current_user: CurrentUser, db: DbSession
) -> dict:
    """用户的第一条地址会自动成为默认地址。"""
    address = create_address(db, current_user.id, payload)
    return success(address, "地址已保存")


@router.put(
    "/{address_id}", response_model=ApiResponse[AddressOut], summary="编辑收货地址"
)
def address_update(
    address_id: int,
    payload: AddressUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """仅更新传入字段，is_default=True 会取消其他默认地址。"""
    address = update_address(db, current_user.id, address_id, payload)
    return success(address, "地址已更新")


@router.delete(
    "/{address_id}", response_model=ApiResponse[dict], summary="删除收货地址"
)
def address_delete(
    address_id: int, current_user: CurrentUser, db: DbSession
) -> dict:
    """删除默认地址后会提升剩余地址中的最新一条为默认。"""
    delete_address(db, current_user.id, address_id)
    return success({"id": address_id}, "地址已删除")

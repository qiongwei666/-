import request from './request'

/** 当前用户的收货地址列表 */
export function getAddresses(config = {}) {
  return request.get('/addresses', config)
}

/** 新增收货地址 */
export function createAddress(data) {
  return request.post('/addresses', data)
}

/** 编辑收货地址 */
export function updateAddress(addressId, data) {
  return request.put(`/addresses/${addressId}`, data)
}

/** 删除收货地址 */
export function deleteAddress(addressId) {
  return request.delete(`/addresses/${addressId}`)
}

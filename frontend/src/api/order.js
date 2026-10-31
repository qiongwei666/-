import request from './request'

/** 从购物车创建订单，可指定收货地址 */
export function createOrder(addressId) {
  const payload = addressId ? { address_id: addressId } : undefined
  return request.post('/orders', payload)
}

/** 获取当前用户的订单列表 */
export function getOrders(config = {}) {
  return request.get('/orders', config)
}

/** 确认收货 */
export function confirmReceipt(orderId) {
  return request.post(`/orders/${orderId}/confirm`)
}

/** 申请退货 / 换货 */
export function requestReturn(orderId, data) {
  return request.post(`/orders/${orderId}/return`, data)
}

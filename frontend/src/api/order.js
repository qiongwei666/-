import request from './request'

/** 从购物车创建订单（无请求体） */
export function createOrder() {
  return request.post('/orders')
}

/** 获取当前用户的订单列表 */
export function getOrders(config = {}) {
  return request.get('/orders', config)
}

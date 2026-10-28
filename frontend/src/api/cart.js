import request from './request'

/** 获取购物车 */
export function getCart(config = {}) {
  return request.get('/cart', config)
}

/** 加入购物车 */
export function addToCart(data, config = {}) {
  return request.post('/cart', data, config)
}

/** 修改购物车条目数量 */
export function updateCartItem(id, data, config = {}) {
  return request.put(`/cart/${id}`, data, config)
}

/** 删除购物车条目 */
export function removeCartItem(id, config = {}) {
  return request.delete(`/cart/${id}`, config)
}

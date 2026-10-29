import request from './request'

/** 后台商品列表 */
export function getAdminProducts(params = {}, config = {}) {
  return request.get('/admin/products', {
    ...config,
    params: {
      page: 1,
      size: 10,
      ...params
    }
  })
}

/** 新增商品 */
export function createAdminProduct(data) {
  return request.post('/admin/products', data)
}

/** 编辑商品 */
export function updateAdminProduct(id, data) {
  return request.put(`/admin/products/${id}`, data)
}

/** 上架 / 下架 */
export function updateProductStatus(id, status) {
  return request.patch(`/admin/products/${id}/status`, { status })
}

/** 后台订单列表 */
export function getAdminOrders(params = {}, config = {}) {
  return request.get('/admin/orders', {
    ...config,
    params: {
      page: 1,
      size: 10,
      ...params
    }
  })
}

/** 订单发货 */
export function shipOrder(id, trackingNo) {
  return request.post(`/admin/orders/${id}/ship`, {
    tracking_no: trackingNo || null
  })
}

/** 审批退换货：approve=true 同意，false 驳回 */
export function reviewReturn(id, approve) {
  return request.post(`/admin/orders/${id}/return-review`, { approve })
}

import request from './request'

/** 获取分类树 */
export function getCategories(config = {}) {
  return request.get('/categories', config)
}

/**
 * 获取商品列表（分页）
 * @param {object} params { page, size, category_id, keyword }
 * @param {object} config axios 配置，例如 { silent: true }
 */
export function getProducts(params = {}, config = {}) {
  return request.get('/products', {
    ...config,
    params: {
      page: 1,
      size: 12,
      ...params
    }
  })
}

/** 获取商品详情 */
export function getProduct(id, config = {}) {
  return request.get(`/products/${id}`, config)
}

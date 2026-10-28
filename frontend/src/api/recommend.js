import request from './request'

/**
 * 个性化推荐（需要登录）
 * @param {object} params { scene: 'home', limit: number }
 */
export function getRecommend(params = {}, config = {}) {
  return request.get('/recommend', {
    ...config,
    params: {
      scene: 'home',
      limit: 10,
      ...params
    }
  })
}

/**
 * 相似商品推荐（看了又看）
 * @param {number|string} productId 当前商品 ID
 * @param {object} params { limit, offset }，offset 用于滚动加载下一批
 * @param {object} config axios 配置
 */
export function getSimilar(productId, params = {}, config = {}) {
  return request.get(`/recommend/similar/${productId}`, {
    ...config,
    params: {
      limit: 8,
      offset: 0,
      ...params
    }
  })
}

/** 热门商品推荐（无需登录，作为未登录时的兜底） */
export function getHot(limit = 10, config = {}) {
  return request.get('/recommend/hot', {
    ...config,
    params: { limit }
  })
}

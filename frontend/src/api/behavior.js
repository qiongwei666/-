import request from './request'

/**
 * 上报用户行为
 * @param {object} data { product_id, behavior_type: 'view' | 'click' | 'cart' | 'buy' }
 * @param {object} config axios 配置，行为上报失败时静默
 */
export function reportBehavior(data, config = { silent: true }) {
  return request.post('/behavior', data, config)
}

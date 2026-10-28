import request from './request'

/** 用户注册 */
export function register(data) {
  return request.post('/auth/register', data)
}

/** 用户登录，返回 { token, token_type, user } */
export function login(data) {
  return request.post('/auth/login', data)
}

/** 获取当前登录用户信息 */
export function getCurrentUser(config = {}) {
  return request.get('/auth/me', config)
}

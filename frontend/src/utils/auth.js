// 登录令牌的本地存储工具

const TOKEN_KEY = 'ecommerce_rec_token'

/** 读取本地令牌 */
export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch (error) {
    return ''
  }
}

/** 保存令牌 */
export function setToken(token) {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  } catch (error) {
    // 忽略隐私模式下的存储异常
  }
}

/** 清除令牌 */
export function removeToken() {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch (error) {
    // 忽略隐私模式下的存储异常
  }
}

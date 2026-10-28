import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from '@/utils/auth'
import { getRouterInstance } from '@/router/instance'

// 统一的 axios 实例：baseURL 可通过环境变量覆盖，默认走 Vite 代理的 /api
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 401 提示去重标记，避免并发请求同时失效时弹出一堆提示
let unauthorizedTimer = null

/** 从后端错误响应中提取可读的错误信息 */
function resolveErrorMessage(data, fallback) {
  if (!data) {
    return fallback
  }
  if (typeof data === 'string') {
    return data
  }
  if (typeof data.message === 'string' && data.message) {
    return data.message
  }
  if (typeof data.detail === 'string' && data.detail) {
    return data.detail
  }
  if (Array.isArray(data.detail) && data.detail.length) {
    const messages = data.detail
      .map((item) => item?.msg || item?.message || '')
      .filter(Boolean)
    if (messages.length) {
      return messages.join('；')
    }
  }
  return fallback
}

/** 统一错误提示，请求配置 silent 为 true 时不打扰用户 */
function showError(config, message) {
  if (config && config.silent) {
    return
  }
  ElMessage.error(message)
}

/**
 * 401 统一处理：清理登录态并跳转登录页
 * 未登录状态下的 401（例如登录接口返回）只做提示，不做跳转
 */
async function handleUnauthorized(config, message = '登录状态已失效，请重新登录') {
  const hadToken = Boolean(getToken())
  removeToken()

  if (!hadToken) {
    if (!unauthorizedTimer) {
      showError(config, message)
    }
    return
  }

  // 通知全局（App.vue）清理用户信息与购物车状态
  window.dispatchEvent(new CustomEvent('app:unauthorized'))

  if (unauthorizedTimer) {
    return
  }
  unauthorizedTimer = window.setTimeout(() => {
    unauthorizedTimer = null
  }, 1500)

  ElMessage.warning('登录状态已失效，请重新登录')

  try {
    // 从独立模块获取路由实例，避免 request 与 router 的循环依赖
    const router = getRouterInstance()
    if (!router) {
      return
    }
    // 使用浏览器地址栏中的地址，确保初始化导航期间也能保留正确的回跳地址
    const currentPath = `${window.location.pathname}${window.location.search}`
    if (window.location.pathname !== '/login') {
      const query =
        currentPath && currentPath !== '/' ? { redirect: currentPath } : {}
      await router.replace({ path: '/login', query })
    }
  } catch (error) {
    // 路由尚未初始化时忽略，后续导航守卫会继续处理登录态
  }
}

// 请求拦截器：自动携带 JWT
service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：解包统一响应 { code, message, data }，并处理业务错误
service.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && Object.prototype.hasOwnProperty.call(body, 'code')) {
      if (body.code === 0) {
        // 直接返回 data，页面无需重复解包
        return body.data
      }

      const message = body.message || '请求失败'
      if (body.code === 401) {
        handleUnauthorized(response.config, message)
        // 标记认证错误，便于 store 在路由守卫阶段同步清理登录态
        const authError = new Error(message)
        authError.isAuthError = true
        return Promise.reject(authError)
      }

      showError(response.config, message)
      return Promise.reject(new Error(message))
    }
    // 非统一结构时原样返回，兼容静态资源等场景
    return body
  },
  (error) => {
    if (axios.isCancel(error)) {
      return Promise.reject(error)
    }

    const status = error.response && error.response.status
    const data = error.response && error.response.data
    const message = resolveErrorMessage(data, error.message || '网络异常')

    if (status === 401) {
      error.isAuthError = true
      handleUnauthorized(error.config, '登录状态已失效，请重新登录')
    } else if (!error.response) {
      showError(error.config, '网络异常，请检查后端服务是否已启动')
    } else {
      showError(error.config, `请求失败（${status}）：${message}`)
    }

    return Promise.reject(error)
  }
)

export default service

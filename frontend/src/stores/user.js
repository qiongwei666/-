import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { getCurrentUser, login as loginApi, register as registerApi } from '@/api/auth'
import { getToken, removeToken, setToken } from '@/utils/auth'

/**
 * 用户状态：token 持久化到 localStorage，刷新后通过 /api/auth/me 恢复用户信息
 */
export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    user: null,
    // 是否已经尝试过恢复用户信息，避免路由守卫重复请求
    profileLoaded: false
  }),

  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    displayName: (state) => state.user?.username || state.user?.email || '用户'
  },

  actions: {
    /** 登录并保存令牌 */
    async login(payload) {
      const data = await loginApi(payload)
      if (!data || !data.token) {
        ElMessage.error('登录失败：响应中缺少令牌')
        throw new Error('登录响应缺少令牌')
      }
      this.setAuth(data.token, data.user)
      // 登录接口未返回用户信息时，主动拉取一次
      if (!this.user) {
        await this.fetchProfile()
      }
      return data
    },

    /** 注册（注册后不自动登录，由页面引导去登录） */
    async register(payload) {
      return registerApi(payload)
    },

    /** 获取当前用户信息 */
    async fetchProfile() {
      if (!this.token) {
        this.profileLoaded = true
        return null
      }
      try {
        const user = await getCurrentUser({ silent: true })
        this.user = user || null
        return this.user
      } catch (error) {
        // 令牌失效时清理本地登录态；网络异常时保留令牌，避免误退出
        const status = error?.response?.status
        if (status === 401 || error?.isAuthError) {
          this.clearAuth()
        }
        return null
      } finally {
        this.profileLoaded = true
      }
    },

    /** 写入登录态 */
    setAuth(token, user) {
      this.token = token || ''
      this.user = user || null
      setToken(this.token)
      this.profileLoaded = Boolean(user)
    },

    /** 清空登录态（本地存储一并清理） */
    clearAuth() {
      this.token = ''
      this.user = null
      this.profileLoaded = false
      removeToken()
    },

    /** 退出登录 */
    logout() {
      this.clearAuth()
    }
  }
})

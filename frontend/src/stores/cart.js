import { defineStore } from 'pinia'
import { addToCart, getCart, removeCartItem, updateCartItem } from '@/api/cart'
import { useUserStore } from './user'

/**
 * 购物车状态：所有写操作成功后重新拉取购物车，保证金额、数量角标与后端一致
 */
export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    totalQuantity: 0,
    totalAmount: 0,
    loading: false,
    loaded: false,
    error: ''
  }),

  getters: {
    isEmpty: (state) => state.items.length === 0,
    count: (state) => state.totalQuantity
  },

  actions: {
    /** 将接口返回的购物车数据写入 state */
    applyCart(data) {
      const items = Array.isArray(data?.items) ? data.items : []
      const quantityFromItems = items.reduce(
        (sum, item) => sum + Number(item?.quantity || 0),
        0
      )
      const amountFromItems = items.reduce(
        (sum, item) => sum + Number(item?.subtotal || 0),
        0
      )

      this.items = items
      this.totalQuantity = Number(
        Number.isFinite(Number(data?.total_quantity))
          ? data.total_quantity
          : quantityFromItems
      )
      this.totalAmount = Number(
        Number.isFinite(Number(data?.total_amount)) ? data.total_amount : amountFromItems
      )
      this.loaded = true
      this.error = ''
    },

    /**
     * 拉取购物车
     * @param {object} options { silent: false 时展示错误提示 }
     */
    async fetchCart(options = {}) {
      const userStore = useUserStore()
      if (!userStore.isLoggedIn) {
        this.reset()
        return null
      }

      this.loading = true
      this.error = ''
      try {
        const data = await getCart({ silent: options.silent === true })
        this.applyCart(data)
        return data
      } catch (error) {
        this.error = error?.message || '购物车加载失败'
        return null
      } finally {
        this.loading = false
        this.loaded = true
      }
    },

    /** 加入购物车，成功后刷新数量角标 */
    async addItem(productId, quantity = 1) {
      const data = await addToCart({
        product_id: Number(productId),
        quantity: Number(quantity) || 1
      })
      await this.fetchCart({ silent: true })
      return data
    },

    /** 修改条目数量 */
    async updateQuantity(id, quantity) {
      const data = await updateCartItem(id, { quantity: Number(quantity) })
      await this.fetchCart({ silent: true })
      return data
    },

    /** 删除条目 */
    async removeItem(id) {
      const data = await removeCartItem(id)
      await this.fetchCart({ silent: true })
      return data
    },

    /** 清空本地购物车状态 */
    reset() {
      this.items = []
      this.totalQuantity = 0
      this.totalAmount = 0
      this.loading = false
      this.loaded = false
      this.error = ''
    }
  }
})

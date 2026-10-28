<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
    <AppFooter />
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useCartStore } from '@/stores/cart'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'

const userStore = useUserStore()
const cartStore = useCartStore()

// 收到 401 通知后清理前端登录态与购物车数据（跳转登录页由 request.js 统一处理）
function handleUnauthorized() {
  userStore.clearAuth()
  cartStore.reset()
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    // 刷新页面后通过 /api/auth/me 恢复用户信息
    if (!userStore.user) {
      userStore.fetchProfile()
    }
    cartStore.fetchCart({ silent: true })
  }
})

// 在 setup 阶段就注册监听，确保子组件更早发出的 401 也能同步清理登录态
window.addEventListener('app:unauthorized', handleUnauthorized)

onBeforeUnmount(() => {
  window.removeEventListener('app:unauthorized', handleUnauthorized)
})

// 登录状态变化时同步购物车：登录后拉取，退出后清空
watch(
  () => userStore.token,
  (token, oldToken) => {
    if (token) {
      if (!userStore.user) {
        userStore.fetchProfile()
      }
      cartStore.fetchCart({ silent: true })
    } else if (oldToken) {
      cartStore.reset()
    }
  }
)
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.app-main {
  flex: 1;
  width: 100%;
  padding: 20px 0 80px;
}
</style>

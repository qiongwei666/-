<template>
  <header class="app-header">
    <div class="header-inner page-container">
      <router-link to="/" class="logo" aria-label="品寻首页">
        <span class="logo-mark">
          <el-icon :size="22"><Goods /></el-icon>
        </span>
        <span class="logo-text">品寻</span>
      </router-link>

      <nav class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="is-active">首页</router-link>
        <router-link to="/products" class="nav-link" active-class="is-active">
          全部商品
        </router-link>
        <router-link
          v-if="userStore.isAdmin"
          to="/admin/products"
          class="nav-link"
          active-class="is-active"
        >
          管理后台
        </router-link>
      </nav>

      <div class="header-actions">
        <router-link to="/cart" class="action-link" aria-label="购物车">
          <el-badge
            :value="cartStore.totalQuantity"
            :max="99"
            :hidden="cartStore.totalQuantity <= 0"
          >
            <el-icon :size="20"><ShoppingCart /></el-icon>
          </el-badge>
          <span class="action-text">购物车</span>
        </router-link>

        <el-dropdown v-if="userStore.isLoggedIn" trigger="click" @command="handleCommand">
          <span class="user-trigger">
            <el-icon><User /></el-icon>
            <span class="user-name">{{ userStore.displayName }}</span>
            <el-icon class="arrow-icon"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="orders">
                <el-icon><Tickets /></el-icon>
                <span>我的订单</span>
              </el-dropdown-item>
              <el-dropdown-item v-if="userStore.isAdmin" command="admin-products">
                <el-icon><Goods /></el-icon>
                <span>商品管理</span>
              </el-dropdown-item>
              <el-dropdown-item v-if="userStore.isAdmin" command="admin-orders">
                <el-icon><Tickets /></el-icon>
                <span>订单管理</span>
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <div v-else class="guest-actions">
          <router-link to="/login" class="login-link">登录</router-link>
          <router-link to="/register">
            <el-button type="primary" plain size="small">注册</el-button>
          </router-link>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const cartStore = useCartStore()

// 用户下拉菜单：我的订单 / 退出登录
function handleCommand(command) {
  if (command === 'orders') {
    router.push('/orders')
    return
  }

  if (command === 'admin-products') {
    router.push('/admin/products')
    return
  }

  if (command === 'admin-orders') {
    router.push('/admin/orders')
    return
  }

  if (command === 'logout') {
    userStore.logout()
    cartStore.reset()
    ElMessage.success('已退出登录')
    // 当前页面需要登录时，退出后跳转到登录页
    if (route.meta.requiresAuth) {
      router.replace({
        path: '/login',
        query: { redirect: route.fullPath }
      })
    }
  }
}
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(251, 251, 253, 0.8);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
}

.header-inner {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.logo-mark {
  width: 24px;
  height: 24px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #1d1d1f;
}

.logo-text {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #1d1d1f;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
}

.nav-link {
  padding: 0;
  color: rgba(0, 0, 0, 0.8);
  font-size: 12px;
  line-height: 48px;
  transition: color 0.2s;
  white-space: nowrap;
}

.nav-link:hover {
  color: #000;
}

.nav-link.is-active {
  color: #000;
  font-weight: 600;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 22px;
}

.action-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: rgba(0, 0, 0, 0.8);
  transition: color 0.2s;
}

.action-link:hover {
  color: #000;
}

.action-text {
  font-size: 12px;
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: rgba(0, 0, 0, 0.8);
  font-size: 12px;
  cursor: pointer;
  outline: none;
  padding: 4px 0;
  max-width: 160px;
}

.user-name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-icon {
  color: #86868b;
  font-size: 11px;
}

.guest-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.login-link {
  color: rgba(0, 0, 0, 0.8);
  font-size: 12px;
}

.login-link:hover {
  color: #000;
}

.guest-actions :deep(.el-button) {
  font-size: 12px;
  height: 26px;
  padding: 0 14px;
}

@media (max-width: 768px) {
  .header-inner {
    height: auto;
    min-height: 52px;
    flex-wrap: wrap;
    gap: 0 16px;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  .logo-mark {
    width: 22px;
    height: 22px;
  }

  .logo-text {
    font-size: 16px;
  }

  .header-actions {
    gap: 16px;
  }

  .nav-links {
    order: 3;
    width: 100%;
    justify-content: center;
    gap: 40px;
    margin-top: 8px;
    padding-top: 10px;
    border-top: 1px solid rgba(0, 0, 0, 0.06);
  }

  .nav-link {
    line-height: 1.5;
    padding: 4px 0;
  }
}

@media (max-width: 480px) {
  .action-text {
    display: none;
  }

  .header-inner {
    gap: 0 10px;
  }

  .guest-actions {
    gap: 10px;
  }

  .logo-text {
    font-size: 15px;
  }

  .nav-links {
    gap: 28px;
  }
}
</style>

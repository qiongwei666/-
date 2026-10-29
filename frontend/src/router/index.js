import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { setRouterInstance } from './instance'

import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import ProductList from '@/views/ProductList.vue'
import ProductDetail from '@/views/ProductDetail.vue'
import Cart from '@/views/Cart.vue'
import Checkout from '@/views/Checkout.vue'
import OrderList from '@/views/OrderList.vue'
import AdminProducts from '@/views/AdminProducts.vue'
import AdminOrders from '@/views/AdminOrders.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { title: '首页' }
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { title: '登录', guestOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: { title: '注册', guestOnly: true }
  },
  {
    path: '/products',
    name: 'products',
    component: ProductList,
    meta: { title: '全部商品' }
  },
  {
    path: '/product/:id',
    name: 'product-detail',
    component: ProductDetail,
    meta: { title: '商品详情' }
  },
  {
    path: '/cart',
    name: 'cart',
    component: Cart,
    meta: { title: '购物车', requiresAuth: true }
  },
  {
    path: '/checkout',
    name: 'checkout',
    component: Checkout,
    meta: { title: '结算', requiresAuth: true }
  },
  {
    path: '/orders',
    name: 'orders',
    component: OrderList,
    meta: { title: '我的订单', requiresAuth: true }
  },
  {
    path: '/admin',
    redirect: '/admin/products'
  },
  {
    path: '/admin/products',
    name: 'admin-products',
    component: AdminProducts,
    meta: { title: '商品管理', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/orders',
    name: 'admin-orders',
    component: AdminOrders,
    meta: { title: '订单管理', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// 注册路由实例，供 axios 响应拦截器处理 401 跳转
setRouterInstance(router)

// 全局前置守卫：恢复登录用户 + 登录校验
router.beforeEach(async (to) => {
  const userStore = useUserStore()

  // 页面刷新后仅有 token 时，通过 /auth/me 恢复用户信息
  if (userStore.token && !userStore.user && !userStore.profileLoaded) {
    await userStore.fetchProfile()
  }

  // 需要登录的页面：未登录跳转登录页，并携带回跳地址
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return {
      path: '/login',
      query: { redirect: to.fullPath }
    }
  }

  // 后台页面：仅管理员可进入
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    ElMessage.warning('需要管理员权限')
    return { path: '/' }
  }

  // 已登录用户不再进入登录 / 注册页
  if (to.meta.guestOnly && userStore.isLoggedIn) {
    return { path: '/' }
  }

  return true
})

// 全局后置守卫：同步页面标题
router.afterEach((to) => {
  const title = to.meta?.title
  document.title = title ? `${title} · 品寻` : '品寻 · 电商推荐系统'
})

export default router

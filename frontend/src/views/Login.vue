<template>
  <div class="page-container auth-page">
    <el-card class="auth-card" shadow="never">
      <div class="auth-header">
        <div class="auth-logo">
          <el-icon :size="26"><Goods /></el-icon>
        </div>
        <h1 class="auth-title">欢迎回来</h1>
        <p class="auth-subtitle">登录后可查看购物车、下单并享受个性化推荐</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model.trim="form.username"
            placeholder="请输入用户名"
            clearable
            autocomplete="username"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            autocomplete="current-password"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            class="submit-button"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link :to="registerLink">立即注册</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: typeof route.query.username === 'string' ? route.query.username : '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 只允许站内路径作为回跳地址，避免开放重定向
const redirectTarget = computed(() => {
  const redirect = route.query.redirect
  if (
    typeof redirect === 'string' &&
    redirect.startsWith('/') &&
    !redirect.startsWith('//') &&
    !redirect.startsWith('/login')
  ) {
    return redirect
  }
  return '/'
})

const registerLink = computed(() => {
  const query = {}
  if (typeof route.query.redirect === 'string') {
    query.redirect = route.query.redirect
  }
  return { path: '/register', query }
})

async function handleSubmit() {
  if (loading.value) {
    return
  }
  // 提前上锁，避免连点导致重复登录请求
  loading.value = true

  try {
    await formRef.value.validate()
  } catch (error) {
    loading.value = false
    return
  }

  try {
    await userStore.login({
      username: form.username,
      password: form.password
    })
    ElMessage.success('登录成功')
    await router.replace(redirectTarget.value)
  } catch (error) {
    // 业务错误提示已由 axios 响应拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-logo {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #1d1d1f;
}

.submit-button {
  width: 100%;
  margin-top: 6px;
  height: 48px;
  font-weight: 500;
}

.auth-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #6e6e73;
}
</style>

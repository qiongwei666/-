<template>
  <div class="page-container auth-page">
    <el-card class="auth-card" shadow="never">
      <div class="auth-header">
        <div class="auth-logo">
          <el-icon :size="26"><UserFilled /></el-icon>
        </div>
        <h1 class="auth-title">创建账号</h1>
        <p class="auth-subtitle">注册品寻账号，开启个性化购物体验</p>
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
            placeholder="请输入用户名（3-20 个字符）"
            clearable
            autocomplete="username"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model.trim="form.email"
            placeholder="请输入邮箱"
            clearable
            autocomplete="email"
          >
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码（至少 6 位）"
            show-password
            autocomplete="new-password"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
            autocomplete="new-password"
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
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        <span>已有账号？</span>
        <router-link :to="loginLink">返回登录</router-link>
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
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 二次密码校验
function validateConfirmPassword(rule, value, callback) {
  if (!value) {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度需为 3-20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度需为 6-32 个字符', trigger: 'blur' }
  ],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }]
}

const loginLink = computed(() => {
  const query = {}
  if (typeof route.query.redirect === 'string') {
    query.redirect = route.query.redirect
  }
  return { path: '/login', query }
})

async function handleSubmit() {
  if (loading.value) {
    return
  }
  // 提前上锁，避免连点导致重复注册请求
  loading.value = true

  try {
    await formRef.value.validate()
  } catch (error) {
    loading.value = false
    return
  }

  try {
    await userStore.register({
      username: form.username,
      password: form.password,
      email: form.email
    })
    ElMessage.success('注册成功，请登录')
    const query = { username: form.username }
    if (typeof route.query.redirect === 'string') {
      query.redirect = route.query.redirect
    }
    router.push({ path: '/login', query })
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

.auth-card :deep(.el-form-item) {
  margin-bottom: 18px;
}
</style>

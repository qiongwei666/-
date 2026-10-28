<template>
  <div class="page-container checkout-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">确认订单</h1>
        <p class="page-subtitle">填写收货信息并确认商品清单，提交后将生成订单</p>
      </div>
      <router-link to="/cart" class="back-link">返回购物车 →</router-link>
    </div>

    <section v-if="loading" class="panel">
      <el-skeleton :rows="5" animated />
    </section>

    <section v-else-if="!cartStore.items.length" class="panel empty-wrap">
      <el-empty description="购物车为空，无法结算" :image-size="100">
        <el-button type="primary" @click="router.push('/products')">去逛商品</el-button>
      </el-empty>
    </section>

    <el-row v-else :gutter="16" class="checkout-layout">
      <!-- 收货信息：仅前端展示与校验，不提交到后端 -->
      <el-col :xs="24" :md="14">
        <section class="panel checkout-form-card">
          <h2 class="block-title">收货信息</h2>
          <el-alert
            title="收货信息仅用于本次演示，不会提交到后端"
            type="info"
            :closable="false"
            show-icon
            class="checkout-alert"
          />

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            size="large"
          >
            <el-form-item label="收货人" prop="receiver">
              <el-input
                v-model.trim="form.receiver"
                placeholder="请输入收货人姓名"
                clearable
                maxlength="20"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="联系电话" prop="phone">
              <el-input
                v-model.trim="form.phone"
                placeholder="请输入联系电话"
                clearable
                maxlength="20"
              >
                <template #prefix>
                  <el-icon><Phone /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="收货地址" prop="address">
              <el-input
                v-model.trim="form.address"
                type="textarea"
                :rows="3"
                placeholder="请输入详细收货地址"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </section>
      </el-col>

      <!-- 商品清单与金额 -->
      <el-col :xs="24" :md="10">
        <aside class="panel order-summary">
          <h2 class="block-title">商品清单</h2>

          <div class="order-items">
            <div v-for="item in cartStore.items" :key="item.id" class="order-item">
              <div class="order-item-image">
                <img
                  :src="item.product?.image_url || PLACEHOLDER_IMAGE"
                  :alt="item.product?.name || '商品'"
                  @error="handleImageError"
                />
              </div>
              <div class="order-item-info">
                <span class="order-item-name">{{ item.product?.name || '商品已下架' }}</span>
                <span class="order-item-price">
                  ¥{{ formatPrice(item.product?.price) }} × {{ item.quantity }}
                </span>
              </div>
              <span class="order-item-subtotal">¥{{ formatPrice(item.subtotal) }}</span>
            </div>
          </div>

          <el-divider />

          <div class="summary-row">
            <span>商品件数</span>
            <span>{{ cartStore.totalQuantity }} 件</span>
          </div>
          <div class="summary-row">
            <span>商品金额</span>
            <span>¥{{ formatPrice(cartStore.totalAmount) }}</span>
          </div>
          <div class="summary-row">
            <span>运费</span>
            <span class="free-shipping">免运费</span>
          </div>

          <el-divider />

          <div class="summary-total">
            <span>应付金额</span>
            <span class="total-amount">¥{{ formatPrice(cartStore.totalAmount) }}</span>
          </div>

          <el-button
            type="primary"
            size="large"
            class="submit-button"
            :loading="submitting"
            :disabled="submitting"
            @click="handleSubmit"
          >
            {{ submitting ? '提交中...' : '提交订单' }}
          </el-button>

          <p class="summary-tip">提交后将由后端从购物车生成订单，请勿重复提交</p>
        </aside>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createOrder } from '@/api/order'
import { useCartStore } from '@/stores/cart'
import { formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const router = useRouter()
const cartStore = useCartStore()

const formRef = ref()
const loading = ref(true)
const submitting = ref(false)

// 收货信息仅做前端展示与校验，不会提交给后端
const form = reactive({
  receiver: '',
  phone: '',
  address: ''
})

const rules = {
  receiver: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '收货人姓名长度需为 2-20 个字符', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    {
      pattern: /^[0-9+\-\s]{6,20}$/,
      message: '请输入正确的联系电话',
      trigger: 'blur'
    }
  ],
  address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' },
    { min: 5, max: 200, message: '收货地址长度需为 5-200 个字符', trigger: 'blur' }
  ]
}

/** 提交订单：无请求体，由后端从购物车结算 */
async function handleSubmit() {
  // 立即上锁，防止表单校验期间重复点击产生重复订单
  if (submitting.value) {
    return
  }
  submitting.value = true

  try {
    await formRef.value.validate()
  } catch (error) {
    submitting.value = false
    return
  }

  if (!cartStore.items.length) {
    submitting.value = false
    ElMessage.warning('购物车为空，无法提交订单')
    return
  }

  try {
    await createOrder()
    // 下单成功后清空本地购物车状态
    cartStore.reset()
    ElMessage.success('订单创建成功')
    // 购买行为由后端订单接口上报，前端不再重复上报 buy
    await router.replace('/orders')
  } catch (error) {
    // 错误提示由 axios 拦截器统一处理
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (cartStore.loaded) {
    loading.value = false
    cartStore.fetchCart({ silent: true })
    return
  }

  await cartStore.fetchCart({ silent: false })
  loading.value = false
})
</script>

<style scoped>
.checkout-page {
  min-height: 60vh;
}

.back-link {
  color: #06c;
  font-size: 14px;
}

.back-link:hover {
  text-decoration: underline;
}

.checkout-layout {
  align-items: flex-start;
}

.checkout-form-card {
  border-radius: 20px;
}

.block-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: #1d1d1f;
  margin-bottom: 18px;
}

.checkout-alert {
  margin-bottom: 20px;
}

.checkout-form-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #6e6e73;
}

.order-summary {
  position: sticky;
  top: 72px;
  border-radius: 20px;
}

.order-items {
  max-height: 320px;
  overflow-y: auto;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f2;
}

.order-item:last-child {
  border-bottom: none;
}

.order-item-image {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  background: #f5f5f7;
}

.order-item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;
}

.order-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.order-item-name {
  font-size: 13px;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.order-item-price {
  font-size: 12px;
  color: #86868b;
}

.order-item-subtotal {
  flex-shrink: 0;
  color: #1d1d1f;
  font-size: 13px;
  font-weight: 600;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6e6e73;
  font-size: 14px;
  margin-bottom: 10px;
}

.free-shipping {
  color: #1a7f37;
}

.summary-total {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  font-weight: 600;
  color: #1d1d1f;
}

.total-amount {
  color: #1d1d1f;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.submit-button {
  width: 100%;
  margin-top: 22px;
  font-weight: 500;
}

.summary-tip {
  margin-top: 12px;
  color: #86868b;
  font-size: 12px;
  text-align: center;
  line-height: 1.6;
}

@media (max-width: 992px) {
  .order-summary {
    position: static;
    margin-top: 16px;
  }
}
</style>

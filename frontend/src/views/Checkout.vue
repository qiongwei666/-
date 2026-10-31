<template>
  <div class="page-container checkout-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">确认订单</h1>
        <p class="page-subtitle">选择收货地址并确认商品清单，提交后将生成订单</p>
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
      <!-- 收货信息：从地址簿选择 -->
      <el-col :xs="24" :md="14">
        <section class="panel checkout-form-card">
          <div class="address-head-row">
            <h2 class="block-title">收货信息</h2>
            <el-button link type="primary" @click="openAddressDialog">
              <el-icon><Plus /></el-icon>
              新增地址
            </el-button>
          </div>

          <div v-if="addressLoading" class="address-loading">
            <el-skeleton :rows="3" animated />
          </div>

          <el-empty
            v-else-if="!addresses.length"
            description="还没有收货地址，请先新增"
            :image-size="80"
            class="address-empty"
          >
            <el-button type="primary" @click="openAddressDialog">
              新增收货地址
            </el-button>
          </el-empty>

          <template v-else>
            <el-radio-group v-model="selectedAddressId" class="address-options">
              <el-radio
                v-for="item in addresses"
                :key="item.id"
                :value="item.id"
                class="address-option"
              >
                <span class="address-option-body">
                  <span class="address-option-head">
                    <span class="address-name">{{ item.receiver_name }}</span>
                    <span class="address-phone">{{ item.phone }}</span>
                    <el-tag
                      v-if="item.is_default"
                      size="small"
                      type="success"
                      effect="light"
                      round
                    >
                      默认
                    </el-tag>
                  </span>
                  <span class="address-text">{{ item.address }}</span>
                </span>
              </el-radio>
            </el-radio-group>

            <router-link to="/addresses" class="manage-link">
              管理收货地址 →
            </router-link>
          </template>
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

    <AddressFormDialog
      v-model="addressDialogVisible"
      :address="editingAddress"
      @saved="handleAddressSaved"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AddressFormDialog from '@/components/AddressFormDialog.vue'
import { getAddresses } from '@/api/address'
import { createOrder } from '@/api/order'
import { useCartStore } from '@/stores/cart'
import { formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const router = useRouter()
const cartStore = useCartStore()

const loading = ref(true)
const submitting = ref(false)

const addresses = ref([])
const addressLoading = ref(true)
const selectedAddressId = ref(null)
const addressDialogVisible = ref(false)
const editingAddress = ref(null)

/** 加载地址簿，默认选中默认地址 */
async function loadAddresses() {
  addressLoading.value = true
  try {
    const data = await getAddresses({ silent: true })
    addresses.value = Array.isArray(data) ? data : []
    if (!addresses.value.some((item) => item.id === selectedAddressId.value)) {
      const fallback =
        addresses.value.find((item) => item.is_default) || addresses.value[0]
      selectedAddressId.value = fallback ? fallback.id : null
    }
  } catch (error) {
    addresses.value = []
    selectedAddressId.value = null
  } finally {
    addressLoading.value = false
  }
}

function openAddressDialog() {
  editingAddress.value = null
  addressDialogVisible.value = true
}

async function handleAddressSaved(saved) {
  await loadAddresses()
  if (saved?.id) {
    selectedAddressId.value = saved.id
  }
}

/** 提交订单：带上选中的收货地址，由后端从购物车结算 */
async function handleSubmit() {
  if (submitting.value) {
    return
  }
  if (!cartStore.items.length) {
    ElMessage.warning('购物车为空，无法提交订单')
    return
  }
  if (!selectedAddressId.value) {
    ElMessage.warning('请选择收货地址')
    return
  }

  submitting.value = true
  try {
    await createOrder(selectedAddressId.value)
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
  const cartRequest = cartStore.loaded
    ? cartStore.fetchCart({ silent: true })
    : cartStore.fetchCart({ silent: false })
  await Promise.all([cartRequest, loadAddresses()])
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

.address-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.address-head-row .block-title {
  margin-bottom: 0;
}

.address-loading {
  padding: 6px 0;
}

.address-empty {
  padding: 8px 0 4px;
}

.address-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.address-option {
  display: flex;
  align-items: flex-start;
  width: 100%;
  height: auto;
  margin-right: 0;
  padding: 14px 16px;
  border: 1px solid #e5e5ea;
  border-radius: 14px;
  transition: border-color 0.2s, background-color 0.2s;
}

.address-option:hover {
  border-color: #c7c7cc;
}

.address-option.is-checked {
  border-color: #0071e3;
  background: #f5f9ff;
}

.address-option :deep(.el-radio__label) {
  flex: 1;
  min-width: 0;
  padding-left: 10px;
}

.address-option-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.address-option-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.address-name {
  color: #1d1d1f;
  font-size: 14px;
  font-weight: 600;
}

.address-phone {
  color: #6e6e73;
  font-size: 13px;
}

.address-text {
  color: #86868b;
  font-size: 13px;
  line-height: 1.6;
  white-space: normal;
  word-break: break-all;
}

.manage-link {
  display: inline-block;
  margin-top: 16px;
  color: #06c;
  font-size: 13px;
}

.manage-link:hover {
  text-decoration: underline;
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

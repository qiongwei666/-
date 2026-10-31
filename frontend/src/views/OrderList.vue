<template>
  <div class="page-container orders-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">我的订单</h1>
        <p class="page-subtitle">查看历史订单与商品明细</p>
      </div>
      <el-button :loading="loading" @click="loadOrders">
        <el-icon><Refresh /></el-icon>
        刷新订单
      </el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="order-list">
      <div v-for="index in 2" :key="index" class="panel order-skeleton">
        <el-skeleton :rows="4" animated />
      </div>
    </div>

    <!-- 加载失败 -->
    <section v-else-if="error" class="panel empty-wrap">
      <el-empty description="订单加载失败，请稍后重试" :image-size="90">
        <el-button type="primary" @click="loadOrders">重新加载</el-button>
      </el-empty>
    </section>

    <!-- 空订单 -->
    <section v-else-if="!orders.length" class="panel empty-wrap">
      <el-empty description="还没有订单，去挑选喜欢的商品吧" :image-size="100">
        <el-button type="primary" @click="router.push('/products')">去购物</el-button>
      </el-empty>
    </section>

    <!-- 订单列表 -->
    <div v-else class="order-list">
      <el-card
        v-for="order in orders"
        :key="order.id"
        class="order-card"
        shadow="never"
      >
        <div class="order-head">
          <div class="order-head-left">
            <span class="order-no">订单号：{{ order.id }}</span>
            <span class="order-time">
              <el-icon><Clock /></el-icon>
              {{ formatDateTime(order.created_at) }}
            </span>
            <span v-if="order.tracking_no" class="order-tracking">
              快递单号：{{ order.tracking_no }}
            </span>
          </div>
          <el-tag :type="getOrderStatus(order.status).type" effect="light" round>
            {{ getOrderStatus(order.status).text }}
          </el-tag>
        </div>

        <div
          v-if="order.receiver_name || order.receiver_phone || order.receiver_address"
          class="order-address"
        >
          <el-icon><Location /></el-icon>
          <span>
            收货信息：{{ order.receiver_name }} {{ order.receiver_phone }}
            <span v-if="order.receiver_address" class="address-detail">
              · {{ order.receiver_address }}
            </span>
          </span>
        </div>

        <div class="order-goods">
          <div v-if="!order.items || !order.items.length" class="order-goods-empty">
            暂无商品明细
          </div>
          <div
            v-for="item in order.items"
            :key="item.id"
            class="order-good"
          >
            <router-link
              v-if="item.product_id"
              :to="`/product/${item.product_id}`"
              class="good-image"
            >
              <img
                :src="item.image_url || PLACEHOLDER_IMAGE"
                :alt="item.product_name || '商品'"
                @error="handleImageError"
              />
            </router-link>
            <div v-else class="good-image">
              <img
                :src="item.image_url || PLACEHOLDER_IMAGE"
                :alt="item.product_name || '商品'"
                @error="handleImageError"
              />
            </div>

            <div class="good-info">
              <router-link
                v-if="item.product_id"
                :to="`/product/${item.product_id}`"
                class="good-name"
              >
                {{ item.product_name || '商品' }}
              </router-link>
              <span v-else class="good-name">{{ item.product_name || '商品' }}</span>
              <span class="good-price">
                ¥{{ formatPrice(item.price) }} × {{ item.quantity }}
              </span>
            </div>

            <span class="good-subtotal">¥{{ formatPrice(item.subtotal) }}</span>
          </div>
        </div>

        <div v-if="order.return_reason" class="order-return">
          退换类型：{{ order.return_type === 'refund' ? '退货退款' : '换货' }}；
          申请原因：{{ order.return_reason }}
        </div>

        <div class="order-foot">
          <div class="order-actions">
            <el-button
              v-if="order.status === 'shipped'"
              size="small"
              type="primary"
              plain
              :loading="confirmingId === order.id"
              @click="handleConfirm(order)"
            >
              确认收货
            </el-button>
            <el-button
              v-if="order.status === 'shipped' || order.status === 'completed'"
              size="small"
              @click="openReturn(order)"
            >
              申请退换货
            </el-button>
          </div>
          <span class="order-count">共 {{ totalCount(order) }} 件商品</span>
          <span class="order-total">
            合计：<strong>¥{{ formatPrice(order.total_amount) }}</strong>
          </span>
        </div>
      </el-card>
    </div>

    <el-dialog v-model="returnVisible" title="申请退货 / 换货" width="460px">
      <p class="return-tip">订单号 #{{ returnOrder?.id }}，提交后由管理员审批。</p>
      <el-form label-position="top">
        <el-form-item label="申请类型">
          <el-radio-group v-model="returnForm.return_type">
            <el-radio value="refund">退货退款</el-radio>
            <el-radio value="exchange">换货</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="申请原因">
          <el-input
            v-model="returnForm.reason"
            type="textarea"
            :rows="3"
            maxlength="255"
            show-word-limit
            placeholder="请说明退换货原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingReturn" @click="submitReturn">
          提交申请
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { confirmReceipt, getOrders, requestReturn } from '@/api/order'
import { formatDateTime, formatPrice, getOrderStatus } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const router = useRouter()

const orders = ref([])
const loading = ref(true)
const error = ref(false)
const confirmingId = ref(null)

const returnVisible = ref(false)
const returnOrder = ref(null)
const submittingReturn = ref(false)
const returnForm = reactive({
  return_type: 'refund',
  reason: ''
})

/** 统计订单内的商品件数 */
function totalCount(order) {
  if (!Array.isArray(order?.items) || !order.items.length) {
    return 0
  }
  return order.items.reduce((sum, item) => sum + Number(item.quantity || 0), 0)
}

/** 加载订单列表 */
async function loadOrders() {
  loading.value = true
  error.value = false

  try {
    const data = await getOrders({ silent: true })
    if (Array.isArray(data)) {
      orders.value = data
    } else if (data && Array.isArray(data.items)) {
      orders.value = data.items
    } else {
      orders.value = []
    }
  } catch (requestError) {
    orders.value = []
    error.value = true
  } finally {
    loading.value = false
  }
}

/** 确认收货 */
async function handleConfirm(order) {
  try {
    await ElMessageBox.confirm('确认已经收到商品？', '确认收货', {
      type: 'info',
      confirmButtonText: '确认收货',
      cancelButtonText: '取消'
    })
  } catch (error) {
    return
  }

  confirmingId.value = order.id
  try {
    await confirmReceipt(order.id)
    ElMessage.success('已确认收货')
    await loadOrders()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    confirmingId.value = null
  }
}

function openReturn(order) {
  returnOrder.value = order
  returnForm.return_type = 'refund'
  returnForm.reason = ''
  returnVisible.value = true
}

/** 提交退货 / 换货申请 */
async function submitReturn() {
  const reason = returnForm.reason.trim()
  if (!reason) {
    ElMessage.warning('请填写申请原因')
    return
  }
  if (!returnOrder.value) {
    return
  }

  submittingReturn.value = true
  try {
    await requestReturn(returnOrder.value.id, {
      return_type: returnForm.return_type,
      reason
    })
    ElMessage.success('申请已提交，等待管理员审批')
    returnVisible.value = false
    await loadOrders()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    submittingReturn.value = false
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.orders-page {
  min-height: 60vh;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.order-card {
  border-radius: 20px;
  border: 1px solid var(--apple-border);
  overflow: hidden;
}

.order-card :deep(.el-card__body) {
  padding: 0;
}

.order-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 22px;
  background: #f5f5f7;
  border-bottom: 1px solid #f0f0f2;
  flex-wrap: wrap;
}

.order-head-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.order-no {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}

.order-time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #86868b;
  font-size: 12px;
}

.order-tracking {
  color: #86868b;
  font-size: 12px;
}

.order-address {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 12px 22px 0;
  color: #6e6e73;
  font-size: 13px;
  line-height: 1.6;
}

.order-address .el-icon {
  margin-top: 3px;
  color: #86868b;
}

.address-detail {
  color: #86868b;
}

.order-goods {
  padding: 4px 22px;
}

.order-goods-empty {
  padding: 18px 0;
  color: #86868b;
  font-size: 13px;
}

.order-good {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f2;
}

.order-good:last-child {
  border-bottom: none;
}

.good-image {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f5f7;
}

.good-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;
}

.good-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.good-name {
  color: #1d1d1f;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

a.good-name:hover {
  color: #06c;
}

.good-price {
  color: #86868b;
  font-size: 12px;
}

.good-subtotal {
  flex-shrink: 0;
  color: #1d1d1f;
  font-size: 14px;
  font-weight: 600;
}

.order-return {
  margin: 0 22px 4px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff8eb;
  color: #8a5a00;
  font-size: 13px;
}

.order-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
  padding: 14px 22px;
  border-top: 1px solid #f0f0f2;
  flex-wrap: wrap;
}

.order-actions {
  margin-right: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.return-tip {
  margin-bottom: 14px;
  color: #6e6e73;
  font-size: 13px;
}

.order-count {
  color: #86868b;
  font-size: 13px;
}

.order-total {
  color: #6e6e73;
  font-size: 14px;
}

.order-total strong {
  color: #1d1d1f;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.order-skeleton {
  border-radius: 20px;
}

@media (max-width: 768px) {
  .order-head,
  .order-address,
  .order-goods,
  .order-foot {
    padding-left: 16px;
    padding-right: 16px;
  }

  .order-good {
    gap: 10px;
  }

  .good-image {
    width: 54px;
    height: 54px;
  }

  .order-total strong {
    font-size: 18px;
  }
}
</style>

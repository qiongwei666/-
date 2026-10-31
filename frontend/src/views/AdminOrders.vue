<template>
  <div class="page-container admin-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">订单管理</h1>
        <p class="page-subtitle">处理发货与退换货审批，可展开查看商品明细</p>
      </div>
      <el-button :loading="loading" @click="loadOrders">
        <el-icon><Refresh /></el-icon>
        刷新订单
      </el-button>
    </div>

    <section class="panel admin-panel">
      <div class="admin-toolbar">
        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          class="status-select"
          @change="handleStatusChange"
        >
          <el-option
            v-for="option in STATUS_OPTIONS"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        <span class="toolbar-count">共 {{ total }} 笔订单</span>
      </div>

      <el-table
        :data="orders"
        v-loading="loading"
        row-key="id"
        stripe
        class="admin-table"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="order-detail">
              <div class="detail-address">
                <span class="detail-address-label">收货信息：</span>
                <span v-if="row.receiver_name || row.receiver_address">
                  {{ row.receiver_name }} {{ row.receiver_phone }}
                  <span class="detail-address-text">{{ row.receiver_address }}</span>
                </span>
                <span v-else class="detail-empty">-</span>
              </div>
              <div v-if="!row.items || !row.items.length" class="detail-empty">
                暂无商品明细
              </div>
              <div
                v-for="item in row.items"
                :key="item.id"
                class="detail-item"
              >
                <img
                  :src="item.image_url || PLACEHOLDER_IMAGE"
                  :alt="item.product_name || '商品'"
                  @error="handleImageError"
                />
                <span class="detail-name">{{ item.product_name || '商品' }}</span>
                <span class="detail-price">
                  ¥{{ formatPrice(item.price) }} × {{ item.quantity }}
                </span>
                <span class="detail-subtotal">¥{{ formatPrice(item.subtotal) }}</span>
              </div>
              <div v-if="row.return_reason" class="return-info">
                退换类型：{{ returnTypeText(row.return_type) }}
                <span class="return-reason">申请原因：{{ row.return_reason }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="订单号" width="100">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column label="金额" width="120">
          <template #default="{ row }">¥{{ formatPrice(row.total_amount) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getOrderStatus(row.status).type" effect="light" round>
              {{ getOrderStatus(row.status).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="快递单号" min-width="150">
          <template #default="{ row }">{{ row.tracking_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'paid'"
              link
              type="primary"
              @click="openShip(row)"
            >
              发货
            </el-button>
            <el-button
              v-else-if="row.status === 'return_pending'"
              link
              type="warning"
              @click="openReview(row)"
            >
              处理退换
            </el-button>
            <span v-else class="action-empty">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="prev, pager, next, jumper"
          :current-page="page"
          :page-size="size"
          :total="total"
          :pager-count="5"
          @current-change="handlePageChange"
        />
      </div>
    </section>

    <el-dialog v-model="shipVisible" title="订单发货" width="430px">
      <p class="dialog-tip">订单号 #{{ activeOrder?.id }}，发货后用户可确认收货。</p>
      <el-form label-position="top">
        <el-form-item label="快递单号（可选）">
          <el-input
            v-model="trackingInput"
            maxlength="64"
            placeholder="例如 SF1234567890"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitShip">
          确认发货
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewVisible" title="处理退换货" width="460px">
      <div class="review-summary">
        <p>订单号：#{{ activeOrder?.id }}</p>
        <p>用户申请：{{ returnTypeText(activeOrder?.return_type) }}</p>
        <p>申请原因：{{ activeOrder?.return_reason || '-' }}</p>
      </div>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="danger" plain :loading="submitting" @click="submitReview(false)">
          驳回
        </el-button>
        <el-button type="primary" :loading="submitting" @click="submitReview(true)">
          {{ activeOrder?.return_type === 'refund' ? '同意退款' : '同意换货' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAdminOrders, reviewReturn, shipOrder } from '@/api/admin'
import { formatDateTime, formatPrice, getOrderStatus } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const STATUS_OPTIONS = [
  { label: '已支付（待发货）', value: 'paid' },
  { label: '已发货', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '退换审核中', value: 'return_pending' },
  { label: '已退款', value: 'refunded' },
  { label: '已换货', value: 'exchanged' },
  { label: '退换已驳回', value: 'return_rejected' }
]

const orders = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const statusFilter = ref('')

const shipVisible = ref(false)
const reviewVisible = ref(false)
const submitting = ref(false)
const activeOrder = ref(null)
const trackingInput = ref('')

function returnTypeText(type) {
  if (type === 'refund') {
    return '退货退款'
  }
  if (type === 'exchange') {
    return '换货'
  }
  return '-'
}

/** 加载后台订单 */
async function loadOrders() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const data = await getAdminOrders(params, { silent: true })
    orders.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total) || 0
  } catch (error) {
    orders.value = []
    total.value = 0
    ElMessage.error('订单列表加载失败')
  } finally {
    loading.value = false
  }
}

function handleStatusChange() {
  page.value = 1
  loadOrders()
}

function handlePageChange(newPage) {
  page.value = newPage
  loadOrders()
}

function openShip(order) {
  activeOrder.value = order
  trackingInput.value = ''
  shipVisible.value = true
}

async function submitShip() {
  if (!activeOrder.value) {
    return
  }
  submitting.value = true
  try {
    await shipOrder(activeOrder.value.id, trackingInput.value.trim())
    ElMessage.success('发货成功')
    shipVisible.value = false
    loadOrders()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    submitting.value = false
  }
}

function openReview(order) {
  activeOrder.value = order
  reviewVisible.value = true
}

async function submitReview(approve) {
  if (!activeOrder.value) {
    return
  }

  if (!approve) {
    try {
      await ElMessageBox.confirm('确认驳回该退换货申请？', '驳回申请', {
        type: 'warning',
        confirmButtonText: '确认驳回',
        cancelButtonText: '取消'
      })
    } catch (error) {
      return
    }
  }

  submitting.value = true
  try {
    await reviewReturn(activeOrder.value.id, approve)
    ElMessage.success(approve ? '已同意退换货' : '已驳回退换货')
    reviewVisible.value = false
    loadOrders()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.admin-page {
  min-height: 60vh;
}

.admin-panel {
  padding: 20px 22px;
}

.admin-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.status-select {
  width: 180px;
}

.toolbar-count {
  margin-left: auto;
  color: #86868b;
  font-size: 13px;
}

.admin-table {
  width: 100%;
}

.action-empty {
  color: #c7c7cc;
}

.order-detail {
  padding: 4px 16px 12px 44px;
}

.detail-address {
  margin-bottom: 8px;
  color: #6e6e73;
  font-size: 13px;
}

.detail-address-label {
  color: #1d1d1f;
  font-weight: 500;
}

.detail-address-text {
  margin-left: 8px;
  color: #86868b;
}

.detail-empty {
  color: #86868b;
  font-size: 13px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f2;
}

.detail-item:last-of-type {
  border-bottom: none;
}

.detail-item img {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  object-fit: cover;
  background: #f5f5f7;
}

.detail-name {
  flex: 1;
  min-width: 0;
  color: #1d1d1f;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-price {
  color: #86868b;
  font-size: 12px;
}

.detail-subtotal {
  color: #1d1d1f;
  font-size: 13px;
  font-weight: 600;
}

.return-info {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff8eb;
  color: #8a5a00;
  font-size: 13px;
}

.return-reason {
  margin-left: 12px;
}

.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-tip {
  margin-bottom: 14px;
  color: #6e6e73;
  font-size: 13px;
}

.review-summary p {
  margin-bottom: 8px;
  color: #1d1d1f;
  font-size: 14px;
}

@media (max-width: 768px) {
  .status-select {
    width: 100%;
  }

  .toolbar-count {
    margin-left: 0;
  }

  .pagination-wrap {
    justify-content: center;
  }
}
</style>

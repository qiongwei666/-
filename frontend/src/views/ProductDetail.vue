<template>
  <div class="page-container detail-page">
    <el-breadcrumb separator="/" class="detail-breadcrumb">
      <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/products' }">全部商品</el-breadcrumb-item>
      <el-breadcrumb-item>{{ product?.name || '商品详情' }}</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 加载中 -->
    <section v-if="loading" class="panel detail-skeleton">
      <el-row :gutter="32">
        <el-col :xs="24" :md="10">
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="image" style="width: 100%; height: 360px" />
            </template>
          </el-skeleton>
        </el-col>
        <el-col :xs="24" :md="14">
          <el-skeleton :rows="7" animated />
        </el-col>
      </el-row>
    </section>

    <!-- 加载失败 -->
    <section v-else-if="loadError || !product" class="panel empty-wrap">
      <el-empty description="商品不存在或已下架" :image-size="90">
        <el-button type="primary" @click="router.push('/products')">返回商品列表</el-button>
      </el-empty>
    </section>

    <template v-else>
      <!-- 商品主信息 -->
      <section class="panel detail-main">
        <el-row :gutter="32">
          <el-col :xs="24" :md="10">
            <div class="gallery">
              <img
                :src="imageUrl"
                :alt="product.name"
                class="gallery-image"
                @error="handleImageError"
              />
            </div>
          </el-col>

          <el-col :xs="24" :md="14">
            <div class="detail-info">
              <div class="detail-tags">
                <el-tag v-if="product.category_name" size="small" effect="plain">
                  {{ product.category_name }}
                </el-tag>
                <el-tag v-if="soldOut" size="small" type="info">已售罄</el-tag>
                <el-tag v-else-if="lowStock" size="small" type="warning">
                  库存紧张
                </el-tag>
              </div>

              <h1 class="detail-name">{{ product.name }}</h1>
              <p class="detail-brief">{{ product.description || '暂无商品简介' }}</p>

              <div class="price-box">
                <span class="price-symbol">¥</span>
                <span class="price-number">{{ formatPrice(product.price) }}</span>
              </div>

              <div class="detail-stats">
                <span>销量：{{ product.sales || 0 }}</span>
                <span class="divider">|</span>
                <span>库存：{{ product.stock ?? 0 }}</span>
                <span class="divider">|</span>
                <span>分类：{{ product.category_name || '未分类' }}</span>
              </div>

              <el-divider />

              <div class="quantity-row">
                <span class="quantity-label">购买数量</span>
                <el-input-number
                  v-model="quantity"
                  :min="1"
                  :max="maxQuantity"
                  :disabled="soldOut"
                  controls-position="right"
                />
                <span class="quantity-tip">库存 {{ product.stock ?? 0 }} 件</span>
              </div>

              <div class="detail-actions">
                <el-button
                  type="primary"
                  plain
                  size="large"
                  :loading="adding"
                  :disabled="soldOut || buying"
                  @click="handleAddToCart(false)"
                >
                  <el-icon><ShoppingCart /></el-icon>
                  加入购物车
                </el-button>
                <el-button
                  type="primary"
                  size="large"
                  :loading="buying"
                  :disabled="soldOut || adding"
                  @click="handleAddToCart(true)"
                >
                  立即购买
                </el-button>
              </div>

              <ul class="service-list">
                <li>正品保障</li>
                <li>极速发货</li>
                <li>七天无理由退换</li>
              </ul>
            </div>
          </el-col>
        </el-row>
      </section>

      <!-- 商品详情 -->
      <section class="panel detail-desc">
        <h2 class="desc-title">商品详情</h2>
        <p class="desc-content">{{ product.description || '暂无更多描述' }}</p>

        <div class="desc-meta">
          <div class="desc-meta-item">
            <span class="meta-label">商品编号</span>
            <span class="meta-value">{{ product.id }}</span>
          </div>
          <div class="desc-meta-item">
            <span class="meta-label">上架时间</span>
            <span class="meta-value">{{ formatDateTime(product.created_at) }}</span>
          </div>
          <div class="desc-meta-item">
            <span class="meta-label">所属分类</span>
            <span class="meta-value">{{ product.category_name || '未分类' }}</span>
          </div>
        </div>
      </section>

      <!-- 相似商品推荐：独立加载，不影响主信息 -->
      <section class="section-block">
        <RecommendPanel
          scene="similar"
          :product-id="product.id"
          :limit="8"
          :max-items="24"
          infinite
          title="看了又看"
          subtitle="根据你刚刚浏览的商品，混合 ALS 协同过滤、真实共访与内容相似实时生成"
        />
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProduct } from '@/api/product'
import { reportBehavior } from '@/api/behavior'
import { useUserStore } from '@/stores/user'
import { useCartStore } from '@/stores/cart'
import { formatDateTime, formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'
import RecommendPanel from '@/components/RecommendPanel.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()

const product = ref(null)
const loading = ref(true)
const loadError = ref(false)
const quantity = ref(1)
const adding = ref(false)
const buying = ref(false)

// 已上报浏览行为的商品 ID，避免重复上报
let reportedViewId = null
let requestSeq = 0

const imageUrl = computed(() => product.value?.image_url || PLACEHOLDER_IMAGE)
const soldOut = computed(() => Number(product.value?.stock) <= 0)
const lowStock = computed(() => {
  const stock = Number(product.value?.stock)
  return Number.isFinite(stock) && stock > 0 && stock <= 10
})
const maxQuantity = computed(() => Math.max(1, Number(product.value?.stock) || 0))

/** 上报浏览行为：失败静默，不打扰用户 */
function reportView(productId) {
  // 行为接口需要登录；匿名用户浏览不产生 401 请求
  if (!userStore.isLoggedIn) {
    return
  }
  const id = Number(productId)
  if (!id || reportedViewId === id) {
    return
  }
  reportedViewId = id
  reportBehavior({ product_id: id, behavior_type: 'view' }, { silent: true }).catch(() => {
    // 浏览行为上报失败时静默处理
  })
}

/** 加载商品详情 */
async function loadProduct(id) {
  const seq = ++requestSeq
  loading.value = true
  loadError.value = false
  product.value = null
  quantity.value = 1

  try {
    const data = await getProduct(id, { silent: true })
    if (seq !== requestSeq) {
      return
    }
    if (!data) {
      loadError.value = true
      return
    }
    product.value = data
    // 进入详情页自动上报一次 view 行为（失败静默）
    reportView(data.id || id)
  } catch (error) {
    if (seq !== requestSeq) {
      return
    }
    loadError.value = true
  } finally {
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

/** 未登录时跳转登录页并携带回跳地址 */
function ensureLogin() {
  if (userStore.isLoggedIn) {
    return true
  }
  ElMessage.warning('请先登录后再操作')
  router.push({
    path: '/login',
    query: { redirect: route.fullPath }
  })
  return false
}

/** 加入购物车；goCheckout 为 true 时加购后直接进入结算页 */
async function handleAddToCart(goCheckout) {
  if (!product.value || adding.value || buying.value) {
    return
  }
  if (!ensureLogin()) {
    return
  }
  if (soldOut.value) {
    ElMessage.warning('该商品暂时无货')
    return
  }

  const flag = goCheckout ? buying : adding
  flag.value = true

  try {
    await cartStore.addItem(product.value.id, quantity.value)
    ElMessage.success(goCheckout ? '已加入购物车，正在前往结算' : '已加入购物车')

    // 加购行为上报（失败静默），购物车角标已由 store 刷新
    reportBehavior(
      { product_id: Number(product.value.id), behavior_type: 'cart' },
      { silent: true }
    ).catch(() => {})

    if (goCheckout) {
      await router.push('/checkout')
    }
  } catch (error) {
    // 错误提示由 axios 拦截器统一处理
  } finally {
    flag.value = false
  }
}

// 路由参数变化时重新加载（同一组件复用场景）
watch(
  () => route.params.id,
  (id) => {
    if (id) {
      loadProduct(id)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.detail-page {
  min-height: 60vh;
}

.detail-breadcrumb {
  margin-bottom: 20px;
}

.detail-main {
  padding: 28px;
  border-radius: 24px;
}

.gallery {
  border-radius: 20px;
  overflow: hidden;
  background: #f5f5f7;
  border: none;
  aspect-ratio: 1 / 1;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;
}

.detail-info {
  padding: 4px 4px 0;
}

.detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-name {
  margin-top: 14px;
  font-size: 30px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.015em;
  color: #1d1d1f;
  word-break: break-word;
}

.detail-brief {
  margin-top: 10px;
  color: #6e6e73;
  font-size: 15px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.price-box {
  margin-top: 20px;
  padding: 0;
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: #1d1d1f;
}

.price-symbol {
  font-size: 22px;
  font-weight: 600;
}

.price-number {
  font-size: 40px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.detail-stats {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #86868b;
  font-size: 13px;
  flex-wrap: wrap;
}

.detail-stats .divider {
  color: #d2d2d7;
}

.quantity-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.quantity-label {
  color: #6e6e73;
  font-size: 14px;
}

.quantity-tip {
  color: #86868b;
  font-size: 12px;
}

.detail-actions {
  margin-top: 26px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-actions .el-button {
  min-width: 158px;
}

.service-list {
  margin: 22px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  color: #6e6e73;
  font-size: 13px;
}

.service-list li::before {
  content: '✓';
  margin-right: 6px;
  color: #1d1d1f;
  font-weight: 600;
}

.detail-desc {
  margin-top: 20px;
  padding: 28px;
  border-radius: 24px;
}

.desc-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: #1d1d1f;
  padding-bottom: 14px;
  border-bottom: 1px solid #f0f0f2;
}

.desc-content {
  margin-top: 16px;
  color: #424245;
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.desc-meta {
  margin-top: 22px;
  display: flex;
  gap: 36px;
  flex-wrap: wrap;
  padding-top: 16px;
  border-top: 1px solid #f0f0f2;
}

.desc-meta-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.meta-label {
  color: #86868b;
}

.meta-value {
  color: #424245;
}

.detail-skeleton {
  padding: 28px;
  border-radius: 24px;
}

@media (max-width: 992px) {
  .gallery {
    max-width: 420px;
    margin: 0 auto 24px;
  }
}

@media (max-width: 768px) {
  .detail-main {
    padding: 16px;
    border-radius: 20px;
  }

  .detail-name {
    font-size: 22px;
  }

  .price-number {
    font-size: 32px;
  }

  .detail-actions .el-button {
    flex: 1;
    min-width: 0;
  }

  .detail-desc {
    padding: 20px;
    border-radius: 20px;
  }

  .desc-meta {
    gap: 14px;
    flex-direction: column;
  }
}
</style>

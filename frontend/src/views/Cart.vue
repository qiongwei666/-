<template>
  <div class="page-container cart-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">我的购物车</h1>
        <p class="page-subtitle">调整商品数量，确认后即可去结算</p>
      </div>
      <router-link to="/products" class="continue-link">继续购物 →</router-link>
    </div>

    <!-- 加载中 -->
    <section v-if="cartStore.loading && !cartStore.items.length" class="panel">
      <el-skeleton :rows="4" animated />
    </section>

    <!-- 空购物车 -->
    <section v-else-if="!cartStore.items.length" class="panel empty-wrap">
      <el-alert
        v-if="cartStore.error"
        :title="cartStore.error"
        type="error"
        :closable="false"
        show-icon
        class="cart-error"
      />
      <el-empty description="购物车还是空的，去挑几件喜欢的商品吧" :image-size="100">
        <el-button type="primary" @click="router.push('/products')">去逛商品</el-button>
      </el-empty>
    </section>

    <div v-else class="cart-layout">
      <section class="panel cart-list">
        <div class="cart-list-head">
          <span class="col-product">商品信息</span>
          <span class="col-price">单价</span>
          <span class="col-quantity">数量</span>
          <span class="col-subtotal">小计</span>
          <span class="col-action">操作</span>
        </div>

        <div
          v-for="item in cartStore.items"
          :key="item.id"
          class="cart-item"
        >
          <div class="col-product product-cell">
            <router-link
              v-if="item.product"
              :to="`/product/${item.product_id}`"
              class="item-image"
            >
              <img
                :src="item.product.image_url || PLACEHOLDER_IMAGE"
                :alt="item.product.name"
                @error="handleImageError"
              />
            </router-link>
            <div v-else class="item-image">
              <img :src="PLACEHOLDER_IMAGE" alt="商品已下架" />
            </div>

            <div class="item-info">
              <router-link
                v-if="item.product"
                :to="`/product/${item.product_id}`"
                class="item-name"
              >
                {{ item.product.name }}
              </router-link>
              <span v-else class="item-name item-name--disabled">商品已下架</span>
              <span v-if="item.product?.category_name" class="item-category">
                {{ item.product.category_name }}
              </span>
            </div>
          </div>

          <div class="col-price item-price">
            <span class="mobile-label">单价</span>
            ¥{{ formatPrice(item.product?.price) }}
          </div>

          <div class="col-quantity item-quantity">
            <span class="mobile-label">数量</span>
            <el-input-number
              v-model="item.quantity"
              :min="1"
              :max="maxStock(item)"
              size="small"
              :disabled="updatingId === item.id || removingId === item.id"
              @change="handleQuantityChange(item, $event)"
            />
          </div>

          <div class="col-subtotal item-subtotal">
            <span class="mobile-label">小计</span>
            <span class="subtotal-value">¥{{ formatPrice(item.subtotal) }}</span>
          </div>

          <div class="col-action item-action">
            <el-button
              text
              type="danger"
              size="small"
              :loading="removingId === item.id"
              :disabled="updatingId === item.id"
              @click="handleRemove(item)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </section>

      <!-- 结算摘要 -->
      <aside class="panel cart-summary">
        <h2 class="summary-title">结算信息</h2>

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
          <span>合计</span>
          <span class="total-amount">¥{{ formatPrice(cartStore.totalAmount) }}</span>
        </div>

        <el-button
          type="primary"
          size="large"
          class="checkout-button"
          :disabled="cartStore.loading"
          @click="router.push('/checkout')"
        >
          去结算
        </el-button>

        <p class="summary-tip">提交订单后，系统将根据购物车内容为你生成订单</p>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCartStore } from '@/stores/cart'
import { formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const router = useRouter()
const cartStore = useCartStore()

const updatingId = ref(null)
const removingId = ref(null)

/** 根据库存计算最大可购买数量 */
function maxStock(item) {
  const stock = Number(item.product?.stock)
  if (!Number.isFinite(stock) || stock <= 0) {
    return 99
  }
  return Math.max(1, stock)
}

/** 修改数量：成功后 store 会重新拉取购物车，失败时回滚 */
async function handleQuantityChange(item, value) {
  if (value === null || value === undefined) {
    return
  }
  updatingId.value = item.id
  try {
    await cartStore.updateQuantity(item.id, Number(value))
  } catch (error) {
    // 失败时重新拉取，恢复服务端数量
    await cartStore.fetchCart({ silent: true })
  } finally {
    updatingId.value = null
  }
}

/** 删除购物车条目 */
async function handleRemove(item) {
  try {
    await ElMessageBox.confirm('确定要从购物车中删除该商品吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch (error) {
    return
  }

  removingId.value = item.id
  try {
    await cartStore.removeItem(item.id)
    ElMessage.success('已从购物车删除')
  } catch (error) {
    // 错误提示由拦截器处理
  } finally {
    removingId.value = null
  }
}

onMounted(() => {
  cartStore.fetchCart({ silent: false })
})
</script>

<style scoped>
.cart-page {
  min-height: 60vh;
}

.continue-link {
  color: #06c;
  font-size: 14px;
}

.continue-link:hover {
  text-decoration: underline;
}

.cart-error {
  margin-bottom: 16px;
}

.cart-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}

.cart-list {
  padding: 0;
  overflow: hidden;
  border-radius: 20px;
}

.cart-list-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 100px 140px 110px 80px;
  gap: 10px;
  padding: 13px 22px;
  background: #f5f5f7;
  border-bottom: 1px solid #f0f0f2;
  color: #86868b;
  font-size: 12px;
}

.cart-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 100px 140px 110px 80px;
  gap: 10px;
  align-items: center;
  padding: 18px 22px;
  border-bottom: 1px solid #f0f0f2;
}

.cart-item:last-child {
  border-bottom: none;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.item-image {
  flex-shrink: 0;
  width: 84px;
  height: 84px;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f5f7;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;
}

.item-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-name {
  color: #1d1d1f;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  word-break: break-all;
}

.item-name:hover {
  color: #06c;
}

.item-name--disabled {
  color: #86868b;
}

.item-category {
  color: #86868b;
  font-size: 12px;
}

.item-price {
  color: #424245;
  font-size: 14px;
}

.item-subtotal {
  color: #1d1d1f;
  font-weight: 600;
  font-size: 15px;
}

.mobile-label {
  display: none;
  color: #86868b;
  font-size: 12px;
  margin-right: 6px;
}

.cart-summary {
  position: sticky;
  top: 72px;
  border-radius: 20px;
}

.summary-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: #1d1d1f;
  margin-bottom: 18px;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6e6e73;
  font-size: 14px;
  margin-bottom: 12px;
}

.free-shipping {
  color: #1a7f37;
}

.summary-total {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  color: #1d1d1f;
  font-weight: 600;
}

.total-amount {
  color: #1d1d1f;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.checkout-button {
  width: 100%;
  margin-top: 22px;
  font-weight: 500;
}

.summary-tip {
  margin-top: 12px;
  color: #86868b;
  font-size: 12px;
  line-height: 1.6;
  text-align: center;
}

@media (max-width: 992px) {
  .cart-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .cart-summary {
    position: static;
  }
}

@media (max-width: 768px) {
  .cart-list-head {
    display: none;
  }

  .cart-item {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      'product product'
      'price action'
      'quantity subtotal';
    row-gap: 10px;
    padding: 14px;
  }

  .col-product {
    grid-area: product;
  }

  .col-price {
    grid-area: price;
  }

  .col-quantity {
    grid-area: quantity;
  }

  .col-subtotal {
    grid-area: subtotal;
    text-align: right;
  }

  .col-action {
    grid-area: action;
    text-align: right;
  }

  .mobile-label {
    display: inline;
  }

  .item-image {
    width: 72px;
    height: 72px;
  }

  .item-quantity {
    display: flex;
    align-items: center;
  }
}
</style>

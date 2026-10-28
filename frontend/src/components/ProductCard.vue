<template>
  <router-link
    :to="`/product/${product.id}`"
    class="product-card-link"
    @click="handleClick"
  >
    <el-card shadow="hover" class="product-card" :body-style="{ padding: 0 }">
      <div class="thumb">
        <img
          :src="imageUrl"
          :alt="product.name || '商品图片'"
          loading="lazy"
          @error="handleImageError"
        />
        <span v-if="soldOut" class="thumb-badge thumb-badge--sold">已售罄</span>
        <span v-else-if="lowStock" class="thumb-badge thumb-badge--low">
          仅剩 {{ product.stock }} 件
        </span>
      </div>

      <div class="info">
        <h3 class="name" :title="product.name">{{ product.name || '未命名商品' }}</h3>
        <p class="category">{{ product.category_name || '未分类' }}</p>
        <div class="meta">
          <span class="price"><small>¥</small>{{ formatPrice(product.price) }}</span>
          <span class="sales">已售 {{ product.sales || 0 }}</span>
        </div>
      </div>
    </el-card>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { reportBehavior } from '@/api/behavior'
import { useUserStore } from '@/stores/user'
import { formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const props = defineProps({
  product: {
    type: Object,
    required: true
  }
})

const userStore = useUserStore()

/**
 * 点击商品卡片时上报 click 行为。
 * 详情页还会再上报一次 view，两者共同构成实时共访与离线 ALS 的训练信号。
 */
function handleClick() {
  if (!userStore.isLoggedIn) {
    return
  }
  const productId = Number(props.product?.id)
  if (!productId) {
    return
  }
  reportBehavior(
    { product_id: productId, behavior_type: 'click' },
    { silent: true }
  ).catch(() => {
    // 行为采集失败不阻塞商品跳转
  })
}

const imageUrl = computed(() => props.product?.image_url || PLACEHOLDER_IMAGE)
const soldOut = computed(() => Number(props.product?.stock) <= 0)
const lowStock = computed(() => {
  const stock = Number(props.product?.stock)
  return Number.isFinite(stock) && stock > 0 && stock <= 10
})
</script>

<style scoped>
.product-card-link {
  display: block;
  height: 100%;
}

.product-card {
  height: 100%;
  border-radius: 18px;
  border: 1px solid var(--apple-hairline);
  overflow: hidden;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  transition: transform var(--transition), box-shadow var(--transition),
    border-color var(--transition);
}

.product-card:hover {
  transform: translateY(-2px);
  border-color: transparent;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.1);
}

.thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #f5f5f7;
  overflow: hidden;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  mix-blend-mode: multiply;
  transition: transform 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.product-card:hover .thumb img {
  transform: scale(1.04);
}

.thumb-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 10px;
  border-radius: 980px;
  font-size: 11px;
  color: #fff;
  line-height: 16px;
  backdrop-filter: blur(8px);
}

.thumb-badge--sold {
  background: rgba(29, 29, 31, 0.72);
}

.thumb-badge--low {
  background: rgba(191, 72, 0, 0.88);
}

.info {
  padding: 14px 16px 18px;
}

.name {
  font-size: 15px;
  font-weight: 500;
  line-height: 1.45;
  letter-spacing: -0.01em;
  color: #1d1d1f;
  height: 44px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  word-break: break-all;
}

.category {
  margin-top: 4px;
  font-size: 12px;
  color: #86868b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta {
  margin-top: 10px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.price {
  color: #1d1d1f;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1;
  white-space: nowrap;
}

.price small {
  font-size: 12px;
  margin-right: 1px;
  font-weight: 500;
}

.sales {
  color: #86868b;
  font-size: 12px;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .info {
    padding: 10px 12px 14px;
  }

  .name {
    font-size: 14px;
    height: 41px;
  }

  .price {
    font-size: 16px;
  }
}
</style>

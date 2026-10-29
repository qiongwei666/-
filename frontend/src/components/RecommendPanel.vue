<template>
  <section class="recommend-panel">
    <div class="recommend-header">
      <div class="recommend-title-wrap">
        <div>
          <h2 class="recommend-title">{{ resolvedTitle }}</h2>
          <p class="recommend-subtitle">{{ resolvedSubtitle }}</p>
        </div>
        <el-tag v-if="!loading && strategy" size="small" type="info" effect="plain" class="strategy-tag">
          推荐策略：{{ strategyText }}
        </el-tag>
      </div>
      <span v-if="!loading && items.length" class="recommend-count">
        已展示 {{ items.length }} 件
      </span>
    </div>

    <!-- 首屏加载：独立骨架屏，不阻塞商品主信息 -->
    <div v-if="loading" class="recommend-grid">
      <div v-for="index in skeletonCount" :key="index" class="recommend-skeleton">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="image" style="width: 100%; height: 150px" />
            <div style="padding: 10px 4px 4px">
              <el-skeleton-item variant="h3" style="width: 85%" />
              <el-skeleton-item variant="text" style="width: 55%; margin-top: 8px" />
              <el-skeleton-item variant="text" style="width: 40%; margin-top: 8px" />
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <!-- 请求失败或结果为空：统一展示“暂无推荐”，绝不阻塞页面 -->
    <el-empty
      v-else-if="error || !items.length"
      description="暂无推荐"
      :image-size="72"
      class="recommend-empty"
    />

    <template v-else>
      <div class="recommend-grid">
        <ProductCard v-for="item in items" :key="item.id" :product="item" />
      </div>

      <!-- 滚动到底部自动加载下一批；按钮兼顾无法自动触发的场景 -->
      <div v-if="infinite" class="load-more">
        <el-button
          v-if="hasMore"
          text
          type="primary"
          :loading="loadingMore"
          @click="loadMore"
        >
          {{
            loadMoreError
              ? '加载失败，点击重试'
              : loadingMore
                ? '正在加载更多'
                : scene === 'similar'
                  ? '加载更多相似商品'
                  : '加载更多'
          }}
        </el-button>
        <span v-else class="load-more-end">已经到底了</span>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getHot, getRecommend, getSimilar } from '@/api/recommend'
import { useUserStore } from '@/stores/user'
import ProductCard from '@/components/ProductCard.vue'

const props = defineProps({
  // home：个性化推荐（未登录用热销兜底）；similar：相似商品“看了又看”
  scene: {
    type: String,
    default: 'home',
    validator: (value) => ['home', 'similar'].includes(value)
  },
  productId: {
    type: [String, Number],
    default: null
  },
  limit: {
    type: Number,
    default: 8
  },
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  // 是否开启“滚动到底部加载更多”，详情页相似推荐开启
  infinite: {
    type: Boolean,
    default: false
  },
  // 单个推荐区最多展示多少条，避免无限请求
  maxItems: {
    type: Number,
    default: 24
  },
  // 未登录时跳过热销榜前 N 件（首页上方已展示同样内容）
  anonymousOffset: {
    type: Number,
    default: 0
  }
})

const userStore = useUserStore()

const items = ref([])
const strategy = ref('')
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(false)
const loadMoreError = ref(false)
const hasMore = ref(false)
const nextOffset = ref(0)

// 请求序号，避免快速切换商品时旧请求覆盖新结果
let requestSeq = 0

const pageSize = computed(() => Math.min(Math.max(Number(props.limit) || 8, 1), 20))
const maxItemCount = computed(() => Math.max(pageSize.value, Number(props.maxItems) || 24))
const skeletonCount = computed(() => Math.min(Math.max(pageSize.value, 4), 8))

const resolvedTitle = computed(() => {
  if (props.title) {
    return props.title
  }
  return props.scene === 'similar' ? '看了又看' : '为你推荐'
})

const resolvedSubtitle = computed(() => {
  if (props.subtitle) {
    return props.subtitle
  }
  if (props.scene === 'similar') {
    return '根据你刚刚浏览的商品，混合 ALS 协同过滤、真实共访与内容相似实时生成'
  }
  return userStore.isLoggedIn
    ? '结合你的历史浏览、收藏与购买偏好生成'
    : '登录后解锁个性化推荐，先看看更多热销好物'
})

// 后端推荐策略标识 -> 中文文案
const STRATEGY_LABELS = {
  als: '个性化推荐',
  behavior: '行为偏好推荐',
  item_als: '物品协同过滤',
  hybrid: 'ALS + 行为共访',
  coview: '真实行为共访',
  content: '内容相似',
  category: '同类热销',
  hot: '热销榜单',
  empty: '暂无策略'
}

const strategyText = computed(() => {
  const key = String(strategy.value || '').toLowerCase()
  return STRATEGY_LABELS[key] || strategy.value
})

/** 请求一页数据，首页与详情页都支持 offset 滚动加载 */
async function fetchPage(offset) {
  if (props.scene === 'similar') {
    if (!props.productId) {
      throw new Error('缺少商品 ID')
    }
    return getSimilar(
      props.productId,
      { limit: pageSize.value, offset },
      { silent: true }
    )
  }

  if (userStore.isLoggedIn) {
    return getRecommend(
      { scene: 'home', limit: pageSize.value, offset },
      { silent: true }
    )
  }

  // 未登录时用热销兜底，并跳过页面上方“热销商品”已经展示的前 N 件
  const skip = Math.max(Number(props.anonymousOffset) || 0, 0)
  return getHot(pageSize.value, offset + skip, { silent: true })
}

/** 首屏 / 商品切换时重置并加载 */
async function resetAndLoad() {
  const seq = ++requestSeq
  loading.value = true
  loadingMore.value = false
  error.value = false
  loadMoreError.value = false
  hasMore.value = false
  nextOffset.value = 0
  items.value = []
  strategy.value = ''

  try {
    const data = await fetchPage(0)
    if (seq !== requestSeq) {
      return
    }
    const list = Array.isArray(data?.items) ? data.items : []
    items.value = list
    strategy.value = data?.strategy || ''
    nextOffset.value = list.length
    hasMore.value =
      props.infinite &&
      list.length >= pageSize.value &&
      items.value.length < maxItemCount.value
  } catch (requestError) {
    if (seq !== requestSeq) {
      return
    }
    items.value = []
    strategy.value = ''
    error.value = true
  } finally {
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

/** 滚动加载下一批相似商品 */
async function loadMore() {
  if (
    !props.infinite ||
    loading.value ||
    loadingMore.value ||
    !hasMore.value
  ) {
    return
  }
  const seq = requestSeq
  loadingMore.value = true
  loadMoreError.value = false

  try {
    const data = await fetchPage(nextOffset.value)
    if (seq !== requestSeq) {
      return
    }
    const list = Array.isArray(data?.items) ? data.items : []
    if (!list.length) {
      hasMore.value = false
      return
    }

    const seen = new Set(items.value.map((item) => item.id))
    const fresh = list.filter((item) => !seen.has(item.id))
    items.value = [...items.value, ...fresh]
    nextOffset.value += list.length
    if (!strategy.value && data?.strategy) {
      strategy.value = data.strategy
    }
    hasMore.value =
      list.length >= pageSize.value &&
      items.value.length < maxItemCount.value
  } catch (requestError) {
    // 加载更多失败不影响已经展示的商品，保留重试入口
    if (seq === requestSeq) {
      loadMoreError.value = true
    }
  } finally {
    if (seq === requestSeq) {
      loadingMore.value = false
    }
  }
}

/** 距离页面底部 420px 时自动加载，模拟淘宝“下滑出更多相似商品” */
function handleScroll() {
  if (
    !props.infinite ||
    loading.value ||
    loadingMore.value ||
    !hasMore.value ||
    loadMoreError.value
  ) {
    return
  }
  const scrollBottom =
    window.scrollY + window.innerHeight >=
    document.documentElement.scrollHeight - 420
  if (scrollBottom) {
    loadMore()
  }
}

watch(
  [
    () => props.scene,
    () => props.productId,
    () => props.limit,
    () => props.maxItems,
    () => props.anonymousOffset,
    () => userStore.isLoggedIn
  ],
  () => {
    resetAndLoad()
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.recommend-panel {
  width: 100%;
  min-height: 120px;
}

.recommend-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.recommend-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.recommend-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 28px;
  line-height: 1.2;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #1d1d1f;
}

.recommend-subtitle {
  margin-top: 6px;
  color: #6e6e73;
  font-size: 13px;
  line-height: 1.6;
}

.strategy-tag {
  margin-top: 4px;
  font-weight: 400;
}

.recommend-count {
  color: #86868b;
  font-size: 13px;
  padding-top: 6px;
}

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.recommend-skeleton {
  background: #fff;
  border-radius: 18px;
  overflow: hidden;
  padding-bottom: 10px;
}

.recommend-empty {
  padding: 10px 0;
}

.load-more {
  min-height: 48px;
  padding-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #86868b;
  font-size: 13px;
}

.load-more-end {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #86868b;
}

.load-more-end::before,
.load-more-end::after {
  content: '';
  width: 42px;
  height: 1px;
  background: #d2d2d7;
}

@media (max-width: 992px) {
  .recommend-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .recommend-title {
    font-size: 24px;
  }
}

@media (max-width: 768px) {
  .recommend-title {
    font-size: 21px;
  }

  .recommend-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
}

@media (max-width: 360px) {
  .recommend-grid {
    grid-template-columns: 1fr;
  }
}
</style>

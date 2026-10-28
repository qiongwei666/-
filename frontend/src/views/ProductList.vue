<template>
  <div class="page-container product-list-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">全部商品</h1>
        <p class="page-subtitle">支持分类筛选与关键词搜索，找到心仪好物</p>
      </div>

      <div class="search-bar">
        <el-input
          v-model="keywordInput"
          placeholder="搜索商品名称或关键词"
          clearable
          class="search-input"
          @keyup.enter="applySearch"
          @clear="applySearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="applySearch">搜索</el-button>
      </div>
    </div>

    <div class="list-layout">
      <!-- 分类树筛选 -->
      <aside class="filter-panel panel">
        <h3 class="filter-title">商品分类</h3>

        <div
          class="all-category"
          :class="{ 'is-active': !categoryId }"
          @click="handleAllCategory"
        >
          <el-icon><Menu /></el-icon>
          <span>全部分类</span>
        </div>

        <div v-if="categoriesLoading" class="tree-loading">
          <el-skeleton :rows="4" animated />
        </div>

        <el-tree
          v-else-if="categories.length"
          ref="treeRef"
          class="category-tree"
          :data="categories"
          :props="treeProps"
          node-key="id"
          highlight-current
          :expand-on-click-node="false"
          default-expand-all
          @node-click="handleCategoryClick"
        />

        <p v-else class="tree-empty">暂无分类</p>
      </aside>

      <!-- 商品区域 -->
      <section class="product-area">
        <div class="result-bar panel">
          <div class="result-info">
            <span>共 <strong>{{ total }}</strong> 件商品</span>
            <el-tag v-if="activeCategoryName" size="small" type="info" effect="plain">
              分类：{{ activeCategoryName }}
            </el-tag>
            <el-tag v-if="keyword" size="small" type="info" effect="plain">
              关键词：{{ keyword }}
            </el-tag>
          </div>
          <el-button
            v-if="keyword || categoryId || page > 1"
            text
            size="small"
            type="primary"
            @click="resetFilters"
          >
            清除筛选
          </el-button>
        </div>

        <div v-if="loading" class="product-grid product-grid--content">
          <div v-for="index in 8" :key="index" class="product-skeleton">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="image" style="width: 100%; height: 160px" />
                <div style="padding: 10px 4px 4px">
                  <el-skeleton-item variant="h3" style="width: 85%" />
                  <el-skeleton-item variant="text" style="width: 50%; margin-top: 8px" />
                </div>
              </template>
            </el-skeleton>
          </div>
        </div>

        <div v-else-if="error" class="panel empty-wrap">
          <el-empty description="商品加载失败，请稍后重试" :image-size="80">
            <el-button type="primary" @click="loadProducts">重新加载</el-button>
          </el-empty>
        </div>

        <template v-else-if="products.length">
          <div class="product-grid product-grid--content">
            <ProductCard
              v-for="product in products"
              :key="product.id"
              :product="product"
            />
          </div>

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
        </template>

        <div v-else class="panel empty-wrap">
          <el-empty description="暂无符合条件的商品" :image-size="80">
            <el-button type="primary" plain @click="resetFilters">查看全部商品</el-button>
          </el-empty>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCategories, getProducts } from '@/api/product'
import ProductCard from '@/components/ProductCard.vue'

const route = useRoute()
const router = useRouter()

const treeRef = ref()
const treeProps = { children: 'children', label: 'name' }

const categories = ref([])
const categoriesLoading = ref(true)

const products = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(12)
const keyword = ref('')
const keywordInput = ref('')
const categoryId = ref(null)
const loading = ref(true)
const error = ref(false)

// 请求序号，防止快速切换筛选条件时旧结果覆盖新结果
let requestSeq = 0

const activeCategoryName = computed(() => findCategoryName(categories.value, categoryId.value))

/** 递归查找分类名称 */
function findCategoryName(list, id) {
  if (!id) {
    return ''
  }
  for (const item of list) {
    if (Number(item.id) === Number(id)) {
      return item.name
    }
    if (item.children && item.children.length) {
      const name = findCategoryName(item.children, id)
      if (name) {
        return name
      }
    }
  }
  return ''
}

/** 从路由 query 中读取筛选条件 */
function readQuery(query) {
  const rawPage = Number.parseInt(query.page, 10)
  page.value = Number.isFinite(rawPage) && rawPage > 0 ? rawPage : 1

  const rawSize = Number.parseInt(query.size, 10)
  size.value = Number.isFinite(rawSize) && rawSize > 0 && rawSize <= 60 ? rawSize : 12

  keyword.value = typeof query.keyword === 'string' ? query.keyword.trim() : ''
  keywordInput.value = keyword.value

  const rawCategory = Number.parseInt(query.category_id, 10)
  categoryId.value =
    Number.isFinite(rawCategory) && rawCategory > 0 ? rawCategory : null
}

/** 加载商品列表 */
async function loadProducts() {
  const seq = ++requestSeq
  loading.value = true
  error.value = false

  const params = {
    page: page.value,
    size: size.value
  }
  if (categoryId.value) {
    params.category_id = categoryId.value
  }
  if (keyword.value) {
    params.keyword = keyword.value
  }

  try {
    const data = await getProducts(params, { silent: true })
    if (seq !== requestSeq) {
      return
    }
    products.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total) || 0
  } catch (requestError) {
    if (seq !== requestSeq) {
      return
    }
    products.value = []
    total.value = 0
    error.value = true
  } finally {
    if (seq === requestSeq) {
      loading.value = false
    }
  }
}

/** 加载分类树 */
async function loadCategories() {
  categoriesLoading.value = true
  try {
    const data = await getCategories({ silent: true })
    categories.value = Array.isArray(data) ? data : []
    await nextTick()
    syncTreeCurrent()
  } catch (requestError) {
    categories.value = []
  } finally {
    categoriesLoading.value = false
  }
}

/** 同步分类树选中状态 */
function syncTreeCurrent() {
  if (!treeRef.value) {
    return
  }
  if (categoryId.value) {
    treeRef.value.setCurrentKey(categoryId.value)
  } else {
    treeRef.value.setCurrentKey(null)
  }
}

/** 构造目标查询参数 */
function buildQuery({ category, search, targetPage }) {
  const query = {}
  const categoryValue = category === undefined ? categoryId.value : category
  const searchValue = search === undefined ? keyword.value : search
  const pageValue = targetPage === undefined ? page.value : targetPage

  if (categoryValue) {
    query.category_id = String(categoryValue)
  }
  if (searchValue) {
    query.keyword = searchValue
  }
  if (pageValue > 1) {
    query.page = String(pageValue)
  }
  return query
}

/** 判断目标查询参数与当前路由是否一致 */
function isSameQuery(query) {
  const current = route.query
  const keys = new Set([...Object.keys(current), ...Object.keys(query)])
  for (const key of keys) {
    if (String(current[key] ?? '') !== String(query[key] ?? '')) {
      return false
    }
  }
  return true
}

/** 更新筛选条件：相同条件直接重新加载，否则更新路由 */
function applyQuery(options = {}) {
  const query = buildQuery(options)
  if (isSameQuery(query)) {
    loadProducts()
    return
  }
  router.push({ path: '/products', query })
}

function handleCategoryClick(node) {
  if (Number(node.id) === Number(categoryId.value)) {
    return
  }
  applyQuery({ category: node.id, targetPage: 1 })
}

function handleAllCategory() {
  if (!categoryId.value && !keyword.value) {
    loadProducts()
    return
  }
  applyQuery({ category: null, targetPage: 1 })
}

function applySearch() {
  const value = keywordInput.value.trim()
  if (value === keyword.value && page.value === 1) {
    loadProducts()
    return
  }
  applyQuery({ search: value, targetPage: 1 })
}

function resetFilters() {
  keywordInput.value = ''
  const query = {}
  if (isSameQuery(query)) {
    loadProducts()
    return
  }
  router.push({ path: '/products', query })
}

function handlePageChange(newPage) {
  applyQuery({ targetPage: newPage })
}

// 路由 query 变化（含首次进入）时重新加载商品
watch(
  () => route.query,
  (query) => {
    readQuery(query)
    loadProducts()
    nextTick(syncTreeCurrent)
  },
  { immediate: true, deep: true }
)

// 分类 ID 变化时同步树选中状态
watch(categoryId, () => {
  nextTick(syncTreeCurrent)
})

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.product-list-page {
  min-height: 60vh;
}

.search-bar {
  display: flex;
  gap: 10px;
  width: 380px;
  max-width: 100%;
}

.search-input {
  flex: 1;
}

.list-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.filter-panel {
  position: sticky;
  top: 72px;
  padding: 20px 16px;
}

.filter-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: #1d1d1f;
  margin-bottom: 14px;
  padding-left: 12px;
}

.all-category {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  margin-bottom: 8px;
  border-radius: 10px;
  color: #424245;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.all-category:hover {
  color: #1d1d1f;
  background: #f5f5f7;
}

.all-category.is-active {
  color: #1d1d1f;
  background: #f5f5f7;
  font-weight: 600;
}

.category-tree {
  --el-tree-node-hover-bg-color: #f5f5f7;
  font-size: 14px;
  max-height: 460px;
  overflow-y: auto;
}

.category-tree :deep(.el-tree-node__content) {
  height: 34px;
  border-radius: 8px;
  padding-right: 6px;
}

.category-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  color: #1d1d1f;
  background: #f5f5f7;
  font-weight: 600;
}

.tree-loading {
  padding: 4px;
}

.tree-empty {
  color: #86868b;
  font-size: 13px;
  padding: 8px 4px;
}

.product-area {
  min-width: 0;
}

.result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  margin-bottom: 20px;
  border-radius: 16px;
  flex-wrap: wrap;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  color: #6e6e73;
  font-size: 13px;
}

.result-info strong {
  color: #1d1d1f;
  font-size: 15px;
  font-weight: 600;
  margin: 0 2px;
}

.product-grid--content {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.product-skeleton {
  border-radius: 18px;
  overflow: hidden;
  background: #fff;
  padding-bottom: 12px;
}

.pagination-wrap {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

@media (max-width: 1200px) {
  .product-grid--content {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .list-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .filter-panel {
    position: static;
    padding: 16px 12px;
  }

  .category-tree {
    max-height: 220px;
  }

  .search-bar {
    width: 100%;
  }

  .product-grid--content {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  /* 移动端隐藏跳页输入框，避免分页组件撑出横向滚动 */
  .pagination-wrap :deep(.el-pagination__jump) {
    display: none;
  }

  .pagination-wrap :deep(.el-pager li) {
    min-width: 28px;
  }
}

@media (max-width: 360px) {
  .product-grid--content {
    grid-template-columns: 1fr;
  }
}
</style>

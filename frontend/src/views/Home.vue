<template>
  <div class="home-page">
    <!-- 全宽 Hero：大字号标题 + 产品主图 + 胶囊按钮 -->
    <section class="hero-section">
      <el-carousel height="480px" :interval="6000" arrow="hover" class="hero-carousel">
        <el-carousel-item v-for="banner in banners" :key="banner.id">
          <div class="hero-slide" :class="banner.theme">
            <div class="hero-inner">
              <div class="hero-copy">
                <p class="hero-eyebrow">{{ banner.tag }}</p>
                <h1 class="hero-title">{{ banner.title }}</h1>
                <p class="hero-sub">{{ banner.desc }}</p>
                <div class="hero-actions">
                  <el-button
                    type="primary"
                    size="large"
                    class="hero-cta"
                    @click="router.push(banner.to)"
                  >
                    {{ banner.action }}
                  </el-button>
                </div>
              </div>

              <div class="hero-visual">
                <img :src="banner.image" :alt="banner.title" />
              </div>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </section>

    <div class="page-container home-content">
      <!-- 分类快捷入口 -->
      <section class="section-block">
        <div class="section-header">
          <h2 class="section-title">分类导航</h2>
          <span class="section-more" @click="router.push('/products')">查看全部商品 →</span>
        </div>

        <div v-if="categoriesLoading" class="category-grid">
          <div v-for="index in 4" :key="index" class="category-skeleton">
            <el-skeleton animated>
              <template #template>
                <el-skeleton-item variant="circle" style="width: 44px; height: 44px" />
                <el-skeleton-item variant="text" style="width: 60%; margin-top: 10px" />
              </template>
            </el-skeleton>
          </div>
        </div>

        <div v-else-if="categories.length" class="category-grid">
          <router-link
            v-for="category in categories"
            :key="category.id"
            class="category-card"
            :to="{ path: '/products', query: { category_id: category.id } }"
          >
            <span class="category-icon">
              <el-icon :size="20"><Grid /></el-icon>
            </span>
            <span class="category-info">
              <span class="category-name">{{ category.name }}</span>
              <span class="category-desc">
                {{ category.children && category.children.length ? `${category.children.length} 个子分类` : '精选分类' }}
              </span>
            </span>
            <el-icon class="category-arrow"><ArrowRight /></el-icon>
          </router-link>
        </div>

        <el-empty v-else description="暂无分类" :image-size="64" />
      </section>

      <!-- 热销商品 -->
      <section class="section-block">
        <div class="section-header">
          <h2 class="section-title">热销商品</h2>
          <span class="section-more" @click="router.push('/products')">更多好物 →</span>
        </div>

        <div v-if="hotLoading" class="product-grid">
          <div v-for="index in 4" :key="index" class="product-skeleton">
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

        <div v-else-if="hotProducts.length" class="product-grid">
          <ProductCard v-for="product in hotProducts" :key="product.id" :product="product" />
        </div>

        <el-empty v-else description="暂无热销商品" :image-size="70">
          <el-button size="small" @click="loadHotProducts">重新加载</el-button>
        </el-empty>
      </section>

      <!-- 个性化推荐：组件内部独立请求，滚动到底部继续加载 -->
      <section class="section-block">
        <RecommendPanel
          scene="home"
          :limit="8"
          :max-items="48"
          :anonymous-offset="8"
          infinite
          title="为你推荐"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getCategories, getProducts } from '@/api/product'
import { getHot } from '@/api/recommend'
import ProductCard from '@/components/ProductCard.vue'
import RecommendPanel from '@/components/RecommendPanel.vue'

const router = useRouter()

const banners = [
  {
    id: 1,
    tag: '新品首发',
    title: '发现你的下一件好物。',
    desc: '精选品质商品，个性化推荐懂你所需。',
    action: '立即选购',
    to: '/products',
    theme: 'hero--light',
    image:
      'https://img14.360buyimg.com/n1/jfs/t1/175048/1/5860/123768/608022ccE2b4258c4/5a3baca88ddcab1f.jpg'
  },
  {
    id: 2,
    tag: '限时精选',
    title: '人气好物，一站购齐。',
    desc: '热销榜单实时更新，好价不容错过。',
    action: '查看热销',
    to: '/products',
    theme: 'hero--dark',
    image:
      'https://img.alicdn.com/bao/uploaded/O1CN01ohRGF01hn4LbAJMIi_!!6000000004321-0-yinhe.jpg'
  },
  {
    id: 3,
    tag: '智能推荐',
    title: '越逛越懂你的商城。',
    desc: '登录后解锁专属推荐，发现更多心仪之选。',
    action: '去登录体验',
    to: '/login',
    theme: 'hero--blue',
    image:
      'https://img.alicdn.com/i4/2200676337006/O1CN01EzKWHz21cnXdJLRHw_!!2200676337006.jpg'
  }
]

const categories = ref([])
const categoriesLoading = ref(true)

const hotProducts = ref([])
const hotLoading = ref(true)

// 分类快捷入口只展示前 8 个顶级分类
async function loadCategories() {
  categoriesLoading.value = true
  try {
    const data = await getCategories({ silent: true })
    const list = Array.isArray(data) ? data : []
    categories.value = list.slice(0, 8)
  } catch (error) {
    categories.value = []
  } finally {
    categoriesLoading.value = false
  }
}

// 热销商品：推荐接口失败时回退到普通商品列表
async function loadHotProducts() {
  hotLoading.value = true
  try {
    const data = await getHot(8, 0, { silent: true })
    hotProducts.value = Array.isArray(data?.items) ? data.items : []
  } catch (error) {
    try {
      const data = await getProducts({ page: 1, size: 8 }, { silent: true })
      hotProducts.value = Array.isArray(data?.items) ? data.items : []
    } catch (fallbackError) {
      hotProducts.value = []
    }
  } finally {
    hotLoading.value = false
  }
}

onMounted(() => {
  loadCategories()
  loadHotProducts()
})
</script>

<style scoped>
.hero-section {
  margin-top: -20px;
  background: #f5f5f7;
}

.hero-slide {
  height: 100%;
  display: flex;
  align-items: center;
}

.hero-inner {
  width: 100%;
  max-width: var(--page-width);
  margin: 0 auto;
  padding: 0 40px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 440px);
  align-items: center;
  gap: 48px;
}

.hero-copy {
  max-width: 560px;
}

.hero-eyebrow {
  font-size: 15px;
  font-weight: 600;
  color: #6e6e73;
}

.hero-title {
  margin-top: 10px;
  font-size: 56px;
  line-height: 1.07;
  font-weight: 600;
  letter-spacing: -0.015em;
}

.hero-sub {
  margin-top: 14px;
  font-size: 21px;
  line-height: 1.4;
  color: #6e6e73;
}

.hero-actions {
  margin-top: 28px;
  display: flex;
  align-items: center;
  gap: 26px;
  flex-wrap: wrap;
}

.hero-visual {
  display: flex;
  justify-content: center;
}

.hero-visual img {
  width: 100%;
  max-width: 440px;
  max-height: 360px;
  object-fit: contain;
  border-radius: 24px;
  background: #fff;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
}

.hero--light {
  background: #f5f5f7;
  color: #1d1d1f;
}

.hero--dark {
  background: #000;
  color: #f5f5f7;
}

.hero--dark .hero-eyebrow {
  color: #86868b;
}

.hero--dark .hero-sub {
  color: #a1a1a6;
}

.hero--blue {
  background: linear-gradient(135deg, #0071e3 0%, #2997ff 100%);
  color: #fff;
}

.hero--blue .hero-eyebrow {
  color: rgba(255, 255, 255, 0.75);
}

.hero--blue .hero-sub {
  color: rgba(255, 255, 255, 0.88);
}

.hero--blue .hero-cta {
  background: #fff;
  border-color: #fff;
  color: #0071e3;
}

.hero--blue .hero-cta:hover,
.hero--blue .hero-cta:focus {
  background: #f5f5f7;
  border-color: #f5f5f7;
  color: #0071e3;
}

.hero-section :deep(.el-carousel__indicator) {
  bottom: 18px;
}

.hero-section :deep(.el-carousel__indicator.is-active .el-carousel__button) {
  background-color: #fff;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.16);
}

.hero-section :deep(.el-carousel__arrow) {
  width: 40px;
  height: 40px;
  font-size: 16px;
}

.home-content {
  padding-top: 0;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.category-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 16px;
  background: #fff;
  transition: transform var(--transition), box-shadow var(--transition);
  min-width: 0;
}

.category-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
}

.category-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #1d1d1f;
  background: #f5f5f7;
}

.category-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.category-name {
  font-size: 15px;
  font-weight: 500;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-desc {
  margin-top: 2px;
  font-size: 12px;
  color: #86868b;
}

.category-arrow {
  flex-shrink: 0;
  color: #86868b;
  font-size: 14px;
}

.category-skeleton {
  border-radius: 16px;
  padding: 16px;
  background: #fff;
}

.product-skeleton {
  border-radius: 18px;
  overflow: hidden;
  background: #fff;
  padding-bottom: 12px;
}

@media (max-width: 992px) {
  .category-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .hero-inner {
    grid-template-columns: minmax(0, 1fr) 320px;
    gap: 24px;
    padding: 0 32px;
  }

  .hero-title {
    font-size: 42px;
  }

  .hero-sub {
    font-size: 18px;
  }

  .hero-visual img {
    max-height: 280px;
  }
}

@media (max-width: 768px) {
  .hero-section :deep(.el-carousel__container) {
    height: 400px !important;
  }

  .hero-inner {
    display: block;
    padding: 0 24px;
  }

  .hero-visual {
    display: none;
  }

  .hero-copy {
    max-width: none;
  }

  .hero-title {
    font-size: 34px;
  }

  .hero-sub {
    font-size: 16px;
  }

  .hero-actions {
    margin-top: 22px;
    gap: 18px;
  }

  .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .category-card {
    padding: 12px;
    gap: 10px;
  }

  .category-icon {
    width: 38px;
    height: 38px;
  }

  .category-name {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .category-desc {
    display: none;
  }

  .hero-title {
    font-size: 30px;
  }
}
</style>

<template>
  <div class="page-container admin-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">商品管理</h1>
        <p class="page-subtitle">新增、编辑与上下架商品，商品图片使用外链 URL</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新增商品
      </el-button>
    </div>

    <section class="panel admin-panel">
      <div class="admin-toolbar">
        <el-input
          v-model="keywordInput"
          placeholder="搜索商品名称或描述"
          clearable
          class="keyword-input"
          @keyup.enter="applySearch"
          @clear="applySearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          class="status-select"
          @change="handleStatusChange"
        >
          <el-option label="已上架" value="on_sale" />
          <el-option label="已下架" value="off_sale" />
        </el-select>
        <el-button type="primary" plain @click="applySearch">查询</el-button>
        <span class="toolbar-count">共 {{ total }} 件商品</span>
      </div>

      <el-table :data="products" v-loading="loading" stripe class="admin-table">
        <el-table-column label="图片" width="84">
          <template #default="{ row }">
            <el-image
              :src="row.image_url || PLACEHOLDER_IMAGE"
              fit="cover"
              class="thumb"
            >
              <template #error>
                <img :src="PLACEHOLDER_IMAGE" class="thumb" alt="暂无图片" />
              </template>
            </el-image>
          </template>
        </el-table-column>
        <el-table-column label="商品名称" min-width="220">
          <template #default="{ row }">
            <div class="product-name">{{ row.name }}</div>
            <div class="product-id">ID：{{ row.id }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="120" />
        <el-table-column label="价格" width="110">
          <template #default="{ row }">¥{{ formatPrice(row.price) }}</template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column prop="sales" label="销量" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'on_sale' ? 'success' : 'info'"
              effect="light"
              round
            >
              {{ row.status === 'on_sale' ? '已上架' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'on_sale' ? 'danger' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.status === 'on_sale' ? '下架' : '上架' }}
            </el-button>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑商品' : '新增商品'"
      width="620px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="product-form"
      >
        <el-form-item label="商品名称" prop="name">
          <el-input
            v-model="form.name"
            maxlength="120"
            show-word-limit
            placeholder="例如：星耀 降噪蓝牙耳机 经典款"
          />
        </el-form-item>

        <el-form-item label="所属分类" prop="category_id">
          <el-tree-select
            v-model="form.category_id"
            :data="categoryTree"
            :props="categoryProps"
            node-key="id"
            default-expand-all
            filterable
            placeholder="请选择二级分类"
            class="full-width"
          />
        </el-form-item>

        <div class="form-row">
          <el-form-item label="价格（元）" prop="price">
            <el-input-number
              v-model="form.price"
              :min="0.01"
              :max="99999999.99"
              :precision="2"
              :step="1"
              controls-position="right"
              class="full-width"
            />
          </el-form-item>
          <el-form-item label="库存" prop="stock">
            <el-input-number
              v-model="form.stock"
              :min="0"
              :max="999999"
              :precision="0"
              :step="1"
              controls-position="right"
              class="full-width"
            />
          </el-form-item>
        </div>

        <el-form-item label="商品图片 URL" prop="image_url">
          <el-input
            v-model="form.image_url"
            maxlength="500"
            placeholder="https://example.com/product.jpg"
          />
          <div class="image-preview">
            <img
              :src="form.image_url || PLACEHOLDER_IMAGE"
              alt="图片预览"
              @error="handleImageError"
            />
            <span class="preview-tip">图片预览</span>
          </div>
        </el-form-item>

        <el-form-item label="商品描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="填写卖点、适用场景等信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          {{ editingId ? '保存修改' : '新增并上架' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAdminProduct,
  getAdminProducts,
  updateAdminProduct,
  updateProductStatus
} from '@/api/admin'
import { getCategories } from '@/api/product'
import { formatPrice } from '@/utils/format'
import { PLACEHOLDER_IMAGE, handleImageError } from '@/utils/image'

const IMAGE_URL_PATTERN = /^(https?:\/\/|\/)/

const products = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const keywordInput = ref('')
const keyword = ref('')
const statusFilter = ref('')

const categoryTree = ref([])
const categoryProps = {
  label: 'name',
  value: 'id',
  children: 'children'
}

const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const formRef = ref()

const form = reactive({
  name: '',
  category_id: null,
  price: 99,
  stock: 10,
  image_url: '',
  description: ''
})

const rules = {
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' },
    { max: 120, message: '商品名称不能超过 120 个字符', trigger: 'blur' }
  ],
  category_id: [{ required: true, message: '请选择二级分类', trigger: 'change' }],
  price: [{ required: true, message: '请输入商品价格', trigger: 'change' }],
  stock: [{ required: true, message: '请输入库存数量', trigger: 'change' }],
  image_url: [
    { required: true, message: '请填写商品图片链接', trigger: 'blur' },
    {
      pattern: IMAGE_URL_PATTERN,
      message: '图片链接需以 http://、https:// 或 / 开头',
      trigger: 'blur'
    }
  ]
}

/** 加载后台商品列表 */
async function loadProducts() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (keyword.value) {
      params.keyword = keyword.value
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const data = await getAdminProducts(params, { silent: true })
    products.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total) || 0
  } catch (error) {
    products.value = []
    total.value = 0
    ElMessage.error('商品列表加载失败')
  } finally {
    loading.value = false
  }
}

/** 加载分类树，供新增 / 编辑选择 */
async function loadCategories() {
  try {
    const data = await getCategories({ silent: true })
    categoryTree.value = Array.isArray(data) ? data : []
  } catch (error) {
    categoryTree.value = []
  }
}

function applySearch() {
  keyword.value = keywordInput.value.trim()
  page.value = 1
  loadProducts()
}

function handleStatusChange() {
  page.value = 1
  loadProducts()
}

function handlePageChange(newPage) {
  page.value = newPage
  loadProducts()
}

function resetForm() {
  form.name = ''
  form.category_id = null
  form.price = 99
  form.stock = 10
  form.image_url = ''
  form.description = ''
}

function openCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.name = row.name
  form.category_id = row.category_id
  form.price = Number(row.price)
  form.stock = row.stock
  form.image_url = row.image_url
  form.description = row.description || ''
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) {
    return
  }
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  submitting.value = true
  const payload = {
    name: form.name.trim(),
    category_id: form.category_id,
    price: form.price,
    stock: form.stock,
    image_url: form.image_url.trim(),
    description: form.description.trim()
  }
  try {
    if (editingId.value) {
      await updateAdminProduct(editingId.value, payload)
      ElMessage.success('商品已更新')
    } else {
      await createAdminProduct(payload)
      ElMessage.success('商品已新增并上架')
    }
    dialogVisible.value = false
    loadProducts()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(row) {
  const isOnSale = row.status === 'on_sale'
  if (isOnSale) {
    try {
      await ElMessageBox.confirm(
        '下架后前台将隐藏该商品，并从用户购物车中移除，确认下架？',
        '下架商品',
        { type: 'warning', confirmButtonText: '确认下架', cancelButtonText: '取消' }
      )
    } catch (error) {
      return
    }
  }

  try {
    await updateProductStatus(row.id, isOnSale ? 'off_sale' : 'on_sale')
    ElMessage.success(isOnSale ? '商品已下架' : '商品已上架')
    loadProducts()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  }
}

onMounted(() => {
  loadProducts()
  loadCategories()
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

.keyword-input {
  width: 260px;
}

.status-select {
  width: 140px;
}

.toolbar-count {
  margin-left: auto;
  color: #86868b;
  font-size: 13px;
}

.admin-table {
  width: 100%;
}

.thumb {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  object-fit: cover;
  background: #f5f5f7;
}

.product-name {
  color: #1d1d1f;
  font-size: 14px;
  line-height: 1.4;
}

.product-id {
  color: #86868b;
  font-size: 12px;
  margin-top: 2px;
}

.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.full-width {
  width: 100%;
}

.image-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.image-preview img {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
  background: #f5f5f7;
}

.preview-tip {
  color: #86868b;
  font-size: 12px;
}

@media (max-width: 768px) {
  .keyword-input,
  .status-select {
    width: 100%;
  }

  .toolbar-count {
    margin-left: 0;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .pagination-wrap {
    justify-content: center;
  }
}
</style>

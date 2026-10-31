<template>
  <div class="page-container address-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">收货地址</h1>
        <p class="page-subtitle">管理常用收货地址，结算时可快速选择</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新增收货地址
      </el-button>
    </div>

    <section v-if="loading" class="panel">
      <el-skeleton :rows="4" animated />
    </section>

    <section v-else-if="!addresses.length" class="panel empty-wrap">
      <el-empty description="还没有收货地址，先添加一条吧" :image-size="100">
        <el-button type="primary" @click="openCreate">新增收货地址</el-button>
      </el-empty>
    </section>

    <div v-else class="address-grid">
      <el-card
        v-for="item in addresses"
        :key="item.id"
        class="address-card"
        shadow="never"
      >
        <div class="address-head">
          <span class="address-name">{{ item.receiver_name }}</span>
          <span class="address-phone">{{ item.phone }}</span>
          <el-tag v-if="item.is_default" type="success" effect="light" round>
            默认
          </el-tag>
        </div>

        <p class="address-text">{{ item.address }}</p>

        <div class="address-actions">
          <el-button
            v-if="!item.is_default"
            link
            type="primary"
            :loading="defaultingId === item.id"
            @click="handleDefault(item)"
          >
            设为默认
          </el-button>
          <el-button link @click="openEdit(item)">编辑</el-button>
          <el-button
            link
            type="danger"
            :loading="deletingId === item.id"
            @click="handleDelete(item)"
          >
            删除
          </el-button>
        </div>
      </el-card>
    </div>

    <AddressFormDialog
      v-model="dialogVisible"
      :address="editingAddress"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AddressFormDialog from '@/components/AddressFormDialog.vue'
import { deleteAddress, getAddresses, updateAddress } from '@/api/address'

const addresses = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const editingAddress = ref(null)
const defaultingId = ref(null)
const deletingId = ref(null)

async function loadAddresses() {
  loading.value = true
  try {
    const data = await getAddresses({ silent: true })
    addresses.value = Array.isArray(data) ? data : []
  } catch (error) {
    addresses.value = []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingAddress.value = null
  dialogVisible.value = true
}

function openEdit(item) {
  editingAddress.value = { ...item }
  dialogVisible.value = true
}

async function handleSaved() {
  await loadAddresses()
}

async function handleDefault(item) {
  defaultingId.value = item.id
  try {
    await updateAddress(item.id, { is_default: true })
    ElMessage.success('已设为默认地址')
    await loadAddresses()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    defaultingId.value = null
  }
}

async function handleDelete(item) {
  try {
    await ElMessageBox.confirm(
      `确认删除「${item.receiver_name}」的收货地址？`,
      '删除地址',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
  } catch (error) {
    return
  }

  deletingId.value = item.id
  try {
    await deleteAddress(item.id)
    ElMessage.success('地址已删除')
    await loadAddresses()
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    deletingId.value = null
  }
}

onMounted(() => {
  loadAddresses()
})
</script>

<style scoped>
.address-page {
  min-height: 60vh;
}

.address-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.address-card {
  border-radius: 18px;
  border: 1px solid var(--apple-border);
}

.address-card :deep(.el-card__body) {
  padding: 18px 20px;
}

.address-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.address-name {
  color: #1d1d1f;
  font-size: 15px;
  font-weight: 600;
}

.address-phone {
  color: #6e6e73;
  font-size: 13px;
}

.address-text {
  margin-bottom: 14px;
  color: #6e6e73;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-all;
}

.address-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  border-top: 1px solid #f0f0f2;
  padding-top: 10px;
}
</style>

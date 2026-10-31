<template>
  <el-dialog
    :model-value="modelValue"
    :title="address ? '编辑收货地址' : '新增收货地址'"
    width="460px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="收货人" prop="receiver_name">
        <el-input
          v-model.trim="form.receiver_name"
          maxlength="50"
          placeholder="请输入收货人姓名"
          clearable
        />
      </el-form-item>

      <el-form-item label="联系电话" prop="phone">
        <el-input
          v-model.trim="form.phone"
          maxlength="20"
          placeholder="请输入联系电话"
          clearable
        />
      </el-form-item>

      <el-form-item label="收货地址" prop="address">
        <el-input
          v-model.trim="form.address"
          type="textarea"
          :rows="3"
          maxlength="255"
          show-word-limit
          placeholder="请输入详细收货地址"
        />
      </el-form-item>

      <el-form-item>
        <el-checkbox v-model="form.is_default" :disabled="address?.is_default">
          设为默认地址
        </el-checkbox>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createAddress, updateAddress } from '@/api/address'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  address: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const formRef = ref()
const submitting = ref(false)
const form = reactive({
  receiver_name: '',
  phone: '',
  address: '',
  is_default: false
})

const rules = {
  receiver_name: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' },
    { max: 50, message: '收货人姓名不能超过 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    {
      pattern: /^[0-9+\-\s]{6,20}$/,
      message: '请输入正确的联系电话',
      trigger: 'blur'
    }
  ],
  address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' },
    { min: 5, max: 255, message: '收货地址长度需为 5-255 个字符', trigger: 'blur' }
  ]
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      return
    }
    form.receiver_name = props.address?.receiver_name || ''
    form.phone = props.address?.phone || ''
    form.address = props.address?.address || ''
    form.is_default = props.address?.is_default || false
    formRef.value?.clearValidate()
  }
)

async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  submitting.value = true
  try {
    const payload = {
      receiver_name: form.receiver_name,
      phone: form.phone,
      address: form.address,
      is_default: form.is_default
    }
    const saved = props.address
      ? await updateAddress(props.address.id, payload)
      : await createAddress(payload)
    ElMessage.success(props.address ? '地址已更新' : '地址已保存')
    emit('saved', saved)
    emit('update:modelValue', false)
  } catch (error) {
    // 错误提示由请求拦截器统一展示
  } finally {
    submitting.value = false
  }
}
</script>

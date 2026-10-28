// 金额、时间、订单状态等格式化工具

/** 金额格式化：保留两位小数 */
export function formatPrice(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) {
    return '0.00'
  }
  return number.toFixed(2)
}

/** 金额格式化：千分位 + 两位小数 */
export function formatAmount(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) {
    return '0.00'
  }
  return number.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

/** 时间格式化：YYYY-MM-DD HH:mm */
export function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  const pad = (number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
}

// 订单状态与中文文案、标签颜色的映射
const ORDER_STATUS_MAP = {
  pending: { text: '待支付', type: 'warning' },
  unpaid: { text: '待支付', type: 'warning' },
  created: { text: '已创建', type: 'warning' },
  paid: { text: '已支付', type: 'success' },
  shipped: { text: '已发货', type: 'primary' },
  delivering: { text: '配送中', type: 'primary' },
  completed: { text: '已完成', type: 'success' },
  finished: { text: '已完成', type: 'success' },
  cancelled: { text: '已取消', type: 'info' },
  canceled: { text: '已取消', type: 'info' },
  closed: { text: '已关闭', type: 'info' },
  refunded: { text: '已退款', type: 'danger' }
}

/** 获取订单状态的展示信息 */
export function getOrderStatus(status) {
  const key = String(status || '').toLowerCase()
  if (ORDER_STATUS_MAP[key]) {
    return ORDER_STATUS_MAP[key]
  }
  return {
    text: status || '未知状态',
    type: 'info'
  }
}

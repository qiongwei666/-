// 图片加载失败时的内联 SVG 占位图

const PLACEHOLDER_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
  <rect width="400" height="400" fill="#f5f5f7"/>
  <rect x="120" y="130" width="160" height="120" rx="12" fill="none" stroke="#d2d2d7" stroke-width="8"/>
  <circle cx="165" cy="175" r="14" fill="#d2d2d7"/>
  <path d="M130 240l50-50 38 38 28-24 34 36" fill="none" stroke="#d2d2d7" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="200" y="300" font-family="Microsoft YaHei, PingFang SC, sans-serif" font-size="22" fill="#86868b" text-anchor="middle">暂无图片</text>
</svg>
`

/** 内联 SVG 占位图（data URI，避免外链失效） */
export const PLACEHOLDER_IMAGE =
  'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(PLACEHOLDER_SVG.trim())

/**
 * 图片加载失败处理：替换为占位图，并防止重复触发
 * 用法：<img :src="url" @error="handleImageError" />
 */
export function handleImageError(event) {
  const image = event && event.target
  if (!image || image.dataset.fallbackApplied === '1') {
    return
  }
  image.dataset.fallbackApplied = '1'
  image.src = PLACEHOLDER_IMAGE
}

<template>
  <footer class="app-footer">
    <div class="footer-inner page-container">
      <div class="footer-main">
        <div class="footer-brand">
          <span class="brand-dot"></span>
          品寻
        </div>
      </div>
      <div class="footer-meta">
        <span>© {{ currentYear }} 品寻</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
const currentYear = new Date().getFullYear()
</script>

<style scoped>
.app-footer {
  background: #f5f5f7;
  border-top: 1px solid #d2d2d7;
  padding: 40px 0 48px;
  margin-top: 0;
}

.footer-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}

.brand-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1d1d1f;
}

.footer-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  color: #86868b;
  font-size: 12px;
}

@media (max-width: 640px) {
  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .footer-meta {
    align-items: flex-start;
    padding-top: 16px;
    border-top: 1px solid #d2d2d7;
    width: 100%;
  }
}
</style>

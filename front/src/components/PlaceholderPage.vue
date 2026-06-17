<template>
  <div class="placeholder-page">
    <div class="placeholder-card">
      <el-icon class="placeholder-icon"><Tools /></el-icon>
      <h2>此功能正在建设中</h2>
      <p>敬请期待</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tools } from '@element-plus/icons-vue'
</script>

<style scoped>
.placeholder-page {
  display: flex; align-items: center; justify-content: center;
  min-height: calc(100vh - var(--topbar-height));
  padding: 40px;
}

.placeholder-card {
  text-align: center;
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  padding: 60px 80px;
}

.placeholder-icon {
  font-size: 48px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
}

h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

p { font-size: 14px; color: var(--color-text-secondary); }
</style>

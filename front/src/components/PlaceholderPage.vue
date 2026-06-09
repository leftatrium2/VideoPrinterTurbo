<template>
  <div class="placeholder-page">
    <div class="placeholder-card">
      <el-icon class="placeholder-icon"><Tools /></el-icon>
      <h2 class="placeholder-title">马上完成</h2>
      <p class="placeholder-sub">此功能正在建设中</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tools } from '@element-plus/icons-vue'
</script>

<style scoped>
.placeholder-page {
  min-height: calc(100vh - var(--topbar-height));
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.placeholder-card {
  text-align: center; padding: 60px 80px;
  background: #fff; border-radius: 8px;
  box-shadow: var(--shadow-card); border: 1px solid var(--color-border);
}
.placeholder-icon { font-size: 48px; color: var(--color-text-secondary); margin-bottom: 16px; }
.placeholder-title { font-size: 24px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 8px; }
.placeholder-sub { font-size: 14px; color: var(--color-text-secondary); }
</style>

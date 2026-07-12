<template>
  <header class="topbar">
    <nav class="breadcrumb" aria-label="breadcrumb">
      <template v-for="(crumb, i) in breadcrumbs" :key="i">
        <span v-if="i > 0" class="crumb-sep">
          <el-icon><ArrowRight /></el-icon>
        </span>
        <span :class="i === breadcrumbs.length - 1 ? 'crumb-current' : 'crumb-link'">
          {{ crumb }}
        </span>
      </template>
    </nav>

    <div class="topbar-actions">
      <el-select
        v-model="currentLocale"
        size="small"
        class="lang-select"
        @change="onLocaleChange"
      >
        <el-option value="zh" :label="t('lang.zh')" />
        <el-option value="en" :label="t('lang.en')" />
      </el-select>
      <el-icon class="action-icon"><Bell /></el-icon>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRight, Bell } from '@element-plus/icons-vue'
import { setLocale } from '@/i18n'

defineProps<{ breadcrumbs: string[] }>()

const { t, locale } = useI18n()
const currentLocale = ref(locale.value as 'zh' | 'en')

function onLocaleChange(val: 'zh' | 'en') {
  setLocale(val)
  // 刷新页面以重新拉取接口数据，适配新语言
  window.location.reload()
}
</script>

<style scoped>
.topbar {
  position: fixed; top: 0;
  left: var(--sidebar-width); right: 0;
  height: var(--topbar-height);
  background: #fff; border-bottom: 1px solid var(--color-border);
  z-index: 40; display: flex;
  align-items: center; justify-content: space-between;
  padding: 0 20px;
}

.breadcrumb {
  display: flex; align-items: center; gap: 6px; font-size: 13px;
}
.crumb-link { color: var(--color-text-secondary); }
.crumb-link:hover { color: var(--color-primary); cursor: pointer; }
.crumb-current { color: var(--color-text-primary); font-weight: 500; }
.crumb-sep { display: flex; align-items: center; color: var(--color-text-secondary); font-size: 12px; }

.topbar-actions { display: flex; align-items: center; gap: 16px; }
.action-icon { font-size: 20px; color: var(--color-text-secondary); cursor: pointer; transition: color 0.2s; }
.action-icon:hover { color: var(--color-primary); }

.lang-select { width: 90px; }
</style>

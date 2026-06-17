<template>
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon">
        <el-icon><Film /></el-icon>
      </div>
      <div class="logo-text">
        <h1>VideoPrinterTurbo</h1>
        <p>{{ t('sidebar.managementSuite') }}</p>
      </div>
    </div>

    <nav class="nav">
      <RouterLink to="/add-task" class="nav-item" active-class="nav-item--active">
        <el-icon><Plus /></el-icon>
        <span>{{ t('sidebar.addTask') }}</span>
      </RouterLink>

      <RouterLink to="/tasks" class="nav-item" active-class="nav-item--active">
        <el-icon><List /></el-icon>
        <span>{{ t('sidebar.taskList') }}</span>
      </RouterLink>

      <div class="nav-section-label">{{ t('sidebar.systemSettings') }}</div>

      <RouterLink
        v-for="item in configItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="nav-item--active"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ t(item.labelKey) }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import {
  Film, Plus, List,
  Microphone, MagicStick, Picture, Promotion, Headset,
} from '@element-plus/icons-vue'

const { t } = useI18n()

const configItems = [
  { to: '/settings/asr',            labelKey: 'sidebar.asrConfig',      icon: Microphone },
  { to: '/settings/llm',            labelKey: 'sidebar.llmConfig',      icon: MagicStick },
  { to: '/settings/material',       labelKey: 'sidebar.materialConfig', icon: Picture },
  { to: '/settings/publish-config', labelKey: 'sidebar.publishConfig',  icon: Promotion },
  { to: '/settings/tts-config',     labelKey: 'sidebar.ttsConfig',      icon: Headset },
]
</script>

<style scoped>
.sidebar {
  position: fixed; left: 0; top: 0;
  width: var(--sidebar-width); height: 100%;
  background: #fff; border-right: 1px solid var(--color-border);
  overflow-y: auto; z-index: 50;
}

.logo { display: flex; align-items: center; gap: 12px; padding: 24px; }

.logo-icon {
  width: 32px; height: 32px; border-radius: 4px;
  background: var(--color-primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}

.logo-text h1 { font-size: 14px; font-weight: 600; color: var(--color-primary-dark); line-height: 20px; }
.logo-text p { font-size: 12px; color: var(--color-text-secondary); }

.nav { padding-bottom: 24px; }

.nav-section-label {
  padding: 16px 24px 4px;
  font-size: 12px; font-weight: 500; color: var(--color-text-secondary);
  text-transform: uppercase; letter-spacing: 0.05em;
}

.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 24px;
  color: var(--color-text-regular); font-size: 14px; font-weight: 500;
  text-decoration: none;
  transition: color 0.2s, background 0.2s; cursor: pointer;
}
.nav-item:hover { color: var(--color-primary); background: var(--color-bg-hover); }

.nav-item--active {
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-left: 2px solid var(--color-primary);
  padding-left: 22px;
}
</style>

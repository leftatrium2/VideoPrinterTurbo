<template>
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon">
        <el-icon><Film /></el-icon>
      </div>
      <div class="logo-text">
        <h1>VideoPrinterTurbo</h1>
        <p>Management Suite</p>
      </div>
    </div>

    <nav class="nav">
      <RouterLink to="/one-step" class="nav-item" active-class="nav-item--active">
        <el-icon><Lightning /></el-icon>
        <span>一步完成</span>
      </RouterLink>

      <div class="nav-section-label">工作流</div>

      <RouterLink
        v-for="item in workflowItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="nav-item--active"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </RouterLink>

      <div class="nav-section-label">系统配置</div>

      <RouterLink
        v-for="item in configItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="nav-item--active"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import {
  Film, Lightning,
  Grid, Download, Document, Edit, Headset, Picture, Promotion,
  Setting, Microphone, Search, Share, Tools,
} from '@element-plus/icons-vue'

const workflowItems = [
  { to: '/steps', label: '分步处理', icon: Grid },
  { to: '/steps/download', label: '下载任务', icon: Download },
  { to: '/steps/doc-extract', label: '文档提取', icon: Document },
  { to: '/steps/llm-rewrite', label: 'LLM 改写', icon: Edit },
  { to: '/steps/tts', label: 'TTS 处理', icon: Headset },
  { to: '/steps/material', label: '素材搜索', icon: Picture },
  { to: '/steps/publish', label: '发布', icon: Promotion },
]

const configItems = [
  { to: '/settings', label: '配置', icon: Setting },
  { to: '/settings/asr', label: 'ASR 配置', icon: Microphone },
  { to: '/settings/llm', label: 'LLM 配置', icon: Setting },
  { to: '/settings/material', label: '素材配置', icon: Search },
  { to: '/settings/publish-config', label: '发布配置', icon: Share },
  { to: '/settings/tts-config', label: 'TTS 配置', icon: Tools },
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
  padding: 12px 24px 4px;
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

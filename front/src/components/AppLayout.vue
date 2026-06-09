<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">
          <el-icon><Film /></el-icon>
        </div>
        <div class="logo-text">
          <h1>Backend Admin</h1>
          <p>Management Suite</p>
        </div>
      </div>

      <nav class="nav">
        <div class="nav-section-label">主要任务</div>

        <RouterLink to="/one-step" class="nav-item" active-class="nav-item--active">
          <el-icon><Lightning /></el-icon>
          <span>一步完成</span>
        </RouterLink>

        <div class="nav-group">
          <button class="nav-item nav-toggle" @click="stepsOpen = !stepsOpen">
            <div class="nav-toggle-left">
              <el-icon><Share /></el-icon>
              <span>分步处理</span>
            </div>
            <el-icon class="toggle-arrow" :class="{ open: stepsOpen }"><ArrowDown /></el-icon>
          </button>
          <div v-show="stepsOpen" class="nav-sub">
            <RouterLink
              v-for="item in stepsItems"
              :key="item.to"
              :to="item.to"
              class="nav-subitem"
              active-class="nav-subitem--active"
            >{{ item.label }}</RouterLink>
          </div>
        </div>

        <div class="nav-section-label" style="margin-top: 8px;">系统管理</div>

        <div class="nav-group">
          <button class="nav-item nav-toggle" @click="settingsOpen = !settingsOpen">
            <div class="nav-toggle-left">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </div>
            <el-icon class="toggle-arrow" :class="{ open: settingsOpen }"><ArrowDown /></el-icon>
          </button>
          <div v-show="settingsOpen" class="nav-sub">
            <RouterLink
              v-for="item in settingsItems"
              :key="item.to"
              :to="item.to"
              class="nav-subitem"
              active-class="nav-subitem--active"
            >{{ item.label }}</RouterLink>
          </div>
        </div>
      </nav>
    </aside>

    <!-- 顶栏 -->
    <header class="topbar">
      <nav class="breadcrumb">
        <template v-for="(crumb, i) in breadcrumbs" :key="i">
          <span v-if="i > 0" class="crumb-sep">/</span>
          <span :class="i === breadcrumbs.length - 1 ? 'crumb-current' : 'crumb-link'">{{ crumb }}</span>
        </template>
      </nav>
      <div class="topbar-actions">
        <el-icon class="action-icon"><Bell /></el-icon>
        <el-icon class="action-icon"><QuestionFilled /></el-icon>
        <el-icon class="action-icon"><Setting /></el-icon>
        <div class="user">
          <div class="user-meta">
            <span class="user-name">Admin User</span>
            <span class="user-role">Super Administrator</span>
          </div>
          <el-avatar :size="40" />
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Film, Lightning, Share, Setting, ArrowDown,
  Bell, QuestionFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const stepsOpen = ref(true)
const settingsOpen = ref(false)

const stepsItems = [
  { to: '/steps/download', label: '下载任务' },
  { to: '/steps/doc-extract', label: '文档提取' },
  { to: '/steps/llm-rewrite', label: 'LLM 改写' },
  { to: '/steps/tts', label: 'TTS 处理' },
  { to: '/steps/material', label: '素材搜索' },
  { to: '/steps/publish', label: '发布' },
]

const settingsItems = [
  { to: '/settings/asr', label: 'ASR 配置' },
  { to: '/settings/llm', label: 'LLM 配置' },
  { to: '/settings/material', label: '素材配置' },
  { to: '/settings/publish-config', label: '发布配置' },
  { to: '/settings/tts-config', label: 'TTS 配置' },
]

const breadcrumbs = computed(() => (route.meta.breadcrumb as string[]) ?? [])
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }

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

.logo-text h1 { font-size: 16px; font-weight: 600; color: var(--color-primary-dark); line-height: 24px; }
.logo-text p { font-size: 12px; color: var(--color-text-secondary); }

.nav { padding-bottom: 24px; }

.nav-section-label {
  padding: 8px 24px;
  font-size: 12px; font-weight: 500; color: var(--color-text-secondary);
  text-transform: uppercase; letter-spacing: 0.05em;
}

.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 24px;
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

.nav-toggle { width: 100%; border: none; background: none; justify-content: space-between; }
.nav-toggle-left { display: flex; align-items: center; gap: 12px; }
.toggle-arrow { font-size: 14px; transition: transform 0.2s; }
.toggle-arrow.open { transform: rotate(180deg); }

.nav-subitem {
  display: flex; align-items: center;
  padding: 12px 24px 12px 56px;
  color: var(--color-text-regular); font-size: 14px; font-weight: 500;
  text-decoration: none; transition: color 0.2s, background 0.2s;
}
.nav-subitem:hover { color: var(--color-primary); background: var(--color-bg-hover); }
.nav-subitem--active {
  color: var(--color-primary); font-weight: 600;
  background: var(--color-primary-light);
  border-left: 2px solid var(--color-primary);
  padding-left: 54px;
}

.topbar {
  position: fixed; top: 0;
  left: var(--sidebar-width); right: 0;
  height: var(--topbar-height);
  background: #fff; border-bottom: 1px solid var(--color-border);
  z-index: 40; display: flex;
  align-items: center; justify-content: space-between;
  padding: 0 20px;
}

.breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.crumb-link { color: var(--color-text-secondary); cursor: pointer; }
.crumb-link:hover { color: var(--color-primary); }
.crumb-current { color: var(--color-text-primary); font-weight: 500; }
.crumb-sep { color: var(--color-text-secondary); }

.topbar-actions { display: flex; align-items: center; gap: 16px; }
.action-icon { font-size: 20px; color: var(--color-text-secondary); cursor: pointer; transition: color 0.2s; }
.action-icon:hover { color: var(--color-primary); }

.user { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.user-meta { text-align: right; }
.user-name { display: block; font-size: 14px; font-weight: 500; color: var(--color-text-primary); }
.user-role { display: block; font-size: 12px; color: var(--color-text-secondary); }

.content {
  margin-left: var(--sidebar-width);
  padding-top: var(--topbar-height);
  min-height: 100vh;
}
</style>

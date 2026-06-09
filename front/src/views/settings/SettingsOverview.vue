<template>
  <div class="page-wrapper">
    <h2 class="page-title">系统配置</h2>
    <p class="page-subtitle">管理 API Key、模型选择和全局参数，修改后需重启服务生效</p>

    <el-row :gutter="16">
      <el-col v-for="item in configItems" :key="item.to" :span="8">
        <RouterLink :to="item.to" class="config-card">
          <div class="config-icon"><el-icon :size="24"><component :is="item.icon" /></el-icon></div>
          <div class="config-info">
            <p class="config-name">{{ item.label }}</p>
            <p class="config-desc">{{ item.desc }}</p>
          </div>
          <el-icon class="config-arrow"><ArrowRight /></el-icon>
        </RouterLink>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight, Microphone, Edit, Picture, Share, Headset } from '@element-plus/icons-vue'

const configItems = [
  { to: '/settings/asr', label: 'ASR 配置', icon: Microphone, desc: '转录引擎、Whisper 模型大小、字幕提供方' },
  { to: '/settings/llm', label: 'LLM 配置', icon: Edit, desc: 'LLM 提供商、API Key、模型名称和温度' },
  { to: '/settings/material', label: '素材配置', icon: Picture, desc: 'Pexels / Pixabay API Key 和默认来源' },
  { to: '/settings/publish-config', label: '发布配置', icon: Share, desc: 'TikTok、Instagram 账号凭据和自动发布' },
  { to: '/settings/tts-config', label: 'TTS 配置', icon: Headset, desc: '语音音色、语速、背景音乐音量' },
]
</script>

<style scoped>
.page-wrapper { padding: 20px; }
.page-title { font-size: 24px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--color-text-secondary); margin-bottom: 24px; }

.config-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border-radius: 8px;
  border: 1px solid var(--color-border); box-shadow: var(--shadow-card);
  padding: 20px; margin-bottom: 16px;
  text-decoration: none; color: inherit;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.config-card:hover { border-color: var(--color-primary); box-shadow: 0 4px 16px 0 rgba(64,158,255,0.15); }

.config-icon {
  width: 44px; height: 44px; flex-shrink: 0; border-radius: 8px;
  background: var(--color-primary-light); color: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
}
.config-info { flex: 1; min-width: 0; }
.config-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 4px; }
.config-desc { font-size: 12px; color: var(--color-text-secondary); line-height: 1.5; }
.config-arrow { color: var(--color-text-secondary); flex-shrink: 0; }
</style>

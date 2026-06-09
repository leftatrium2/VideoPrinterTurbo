<template>
  <div class="page-wrapper">
    <h2 class="page-title">分步处理</h2>
    <p class="page-subtitle">按顺序执行各步骤，或直接使用「一步完成」自动运行全流程</p>

    <div class="pipeline">
      <RouterLink
        v-for="(step, i) in steps"
        :key="step.to"
        :to="step.to"
        class="step-card"
      >
        <div class="step-num">{{ i + 1 }}</div>
        <div class="step-icon"><el-icon :size="28"><component :is="step.icon" /></el-icon></div>
        <div class="step-name">{{ step.label }}</div>
        <div class="step-desc">{{ step.desc }}</div>
        <div v-if="i < steps.length - 1" class="step-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </RouterLink>
    </div>

    <div class="shortcut-card">
      <div class="shortcut-left">
        <p class="shortcut-title">想直接跑完全程？</p>
        <p class="shortcut-desc">一步完成会自动依次执行所有步骤，无需手动干预。</p>
      </div>
      <RouterLink to="/one-step">
        <el-button type="primary" size="large">前往一步完成</el-button>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight, Download, Document, Edit, Headset, Picture, Promotion } from '@element-plus/icons-vue'

const steps = [
  { to: '/steps/download', label: '下载任务', icon: Download, desc: '使用 yt-dlp 下载视频、音频和字幕' },
  { to: '/steps/doc-extract', label: '文档提取', icon: Document, desc: '提取内嵌字幕或使用 Whisper ASR 转录' },
  { to: '/steps/llm-rewrite', label: 'LLM 改写', icon: Edit, desc: '用大语言模型重写解说词和搜索词' },
  { to: '/steps/tts', label: 'TTS 处理', icon: Headset, desc: 'Edge TTS 生成语音配音和时间轴字幕' },
  { to: '/steps/material', label: '素材搜索', icon: Picture, desc: '从 Pexels/Pixabay 搜索并下载素材' },
  { to: '/steps/publish', label: '发布', icon: Promotion, desc: 'moviepy 合成最终视频并可选自动发布' },
]
</script>

<style scoped>
.page-wrapper { padding: 20px; }
.page-title { font-size: 24px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--color-text-secondary); margin-bottom: 24px; }

.pipeline {
  display: flex; flex-wrap: wrap; gap: 0;
  background: #fff; border-radius: 8px;
  border: 1px solid var(--color-border); box-shadow: var(--shadow-card);
  overflow: hidden; margin-bottom: 20px;
}

.step-card {
  flex: 1; min-width: 140px;
  position: relative;
  display: flex; flex-direction: column; align-items: center;
  padding: 28px 16px 24px;
  text-decoration: none; color: inherit;
  border-right: 1px solid var(--color-border);
  transition: background 0.2s;
}
.step-card:last-child { border-right: none; }
.step-card:hover { background: var(--color-bg-hover); }

.step-num {
  position: absolute; top: 12px; left: 16px;
  font-size: 11px; font-weight: 700; color: var(--color-primary);
  background: var(--color-primary-light); border-radius: 4px;
  padding: 1px 6px;
}
.step-icon { color: var(--color-primary); margin-bottom: 10px; }
.step-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 6px; text-align: center; }
.step-desc { font-size: 12px; color: var(--color-text-secondary); text-align: center; line-height: 1.6; }

.step-arrow {
  position: absolute; right: -12px; top: 50%;
  transform: translateY(-50%);
  background: #fff; border: 1px solid var(--color-border);
  border-radius: 50%; width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  z-index: 1; color: var(--color-text-secondary); font-size: 12px;
}

.shortcut-card {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border-radius: 8px;
  border: 1px solid var(--color-border); box-shadow: var(--shadow-card);
  padding: 20px 24px;
}
.shortcut-title { font-size: 15px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 4px; }
.shortcut-desc { font-size: 13px; color: var(--color-text-secondary); }
</style>

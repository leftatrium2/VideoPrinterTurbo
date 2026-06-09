import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/one-step',
      children: [
        {
          path: 'one-step',
          component: () => import('@/views/OneStep.vue'),
          meta: { breadcrumb: ['一步完成'] }
        },
        {
          path: 'steps/download',
          component: () => import('@/views/download/DownloadTask.vue'),
          meta: { breadcrumb: ['分步处理', '下载任务'] }
        },
        {
          path: 'steps/doc-extract',
          component: () => import('@/views/steps/DocExtract.vue'),
          meta: { breadcrumb: ['分步处理', '文档提取'] }
        },
        {
          path: 'steps/llm-rewrite',
          component: () => import('@/views/steps/LLMRewrite.vue'),
          meta: { breadcrumb: ['分步处理', 'LLM 改写'] }
        },
        {
          path: 'steps/tts',
          component: () => import('@/views/steps/TTS.vue'),
          meta: { breadcrumb: ['分步处理', 'TTS 处理'] }
        },
        {
          path: 'steps/material',
          component: () => import('@/views/steps/Material.vue'),
          meta: { breadcrumb: ['分步处理', '素材搜索'] }
        },
        {
          path: 'steps/publish',
          component: () => import('@/views/steps/Publish.vue'),
          meta: { breadcrumb: ['分步处理', '发布'] }
        },
        {
          path: 'settings/asr',
          component: () => import('@/views/settings/ASR.vue'),
          meta: { breadcrumb: ['系统设置', 'ASR 配置'] }
        },
        {
          path: 'settings/llm',
          component: () => import('@/views/settings/LLM.vue'),
          meta: { breadcrumb: ['系统设置', 'LLM 配置'] }
        },
        {
          path: 'settings/material',
          component: () => import('@/views/settings/MaterialConfig.vue'),
          meta: { breadcrumb: ['系统设置', '素材配置'] }
        },
        {
          path: 'settings/publish-config',
          component: () => import('@/views/settings/PublishConfig.vue'),
          meta: { breadcrumb: ['系统设置', '发布配置'] }
        },
        {
          path: 'settings/tts-config',
          component: () => import('@/views/settings/TTSConfig.vue'),
          meta: { breadcrumb: ['系统设置', 'TTS 配置'] }
        },
      ]
    }
  ]
})

export default router

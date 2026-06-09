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
          meta: { breadcrumb: ['VideoPrinterTurbo', '一步完成'] }
        },
        {
          path: 'steps',
          component: () => import('@/views/steps/StepsOverview.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', '分步处理'] }
        },
        {
          path: 'steps/download',
          component: () => import('@/views/download/DownloadTask.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', '下载任务'] }
        },
        {
          path: 'steps/doc-extract',
          component: () => import('@/views/steps/DocExtract.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', '文档提取'] }
        },
        {
          path: 'steps/llm-rewrite',
          component: () => import('@/views/steps/LLMRewrite.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', 'LLM 改写'] }
        },
        {
          path: 'steps/tts',
          component: () => import('@/views/steps/TTS.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', 'TTS 处理'] }
        },
        {
          path: 'steps/material',
          component: () => import('@/views/steps/Material.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', '素材搜索'] }
        },
        {
          path: 'steps/publish',
          component: () => import('@/views/steps/Publish.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '工作流', '发布'] }
        },
        {
          path: 'settings',
          component: () => import('@/views/settings/SettingsOverview.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '系统配置', '配置'] }
        },
        {
          path: 'settings/asr',
          component: () => import('@/views/settings/ASR.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '系统配置', 'ASR 配置'] }
        },
        {
          path: 'settings/llm',
          component: () => import('@/views/settings/LLM.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '系统配置', 'LLM 配置'] }
        },
        {
          path: 'settings/material',
          component: () => import('@/views/settings/MaterialConfig.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '系统配置', '素材配置'] }
        },
        {
          path: 'settings/publish-config',
          component: () => import('@/views/settings/PublishConfig.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '系统配置', '发布配置'] }
        },
        {
          path: 'settings/tts-config',
          component: () => import('@/views/settings/TTSConfig.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '系统配置', 'TTS 配置'] }
        },
      ]
    }
  ]
})

export default router

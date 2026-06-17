import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/add-task',
      children: [
        {
          path: 'add-task',
          component: () => import('@/views/AddTask.vue'),
          meta: { breadcrumb: ['添加任务', '添加新任务'] }
        },
        {
          path: 'tasks',
          component: () => import('@/views/TaskList.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '任务列表'] }
        },
        {
          path: 'settings/asr',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '配置', 'ASR 配置'] }
        },
        {
          path: 'settings/llm',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '配置', 'LLM 配置'] }
        },
        {
          path: 'settings/material',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '配置', '素材配置'] }
        },
        {
          path: 'settings/publish-config',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '配置', '发布配置'] }
        },
        {
          path: 'settings/tts-config',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['VideoPrinterTurbo', '配置', 'TTS 配置'] }
        },
      ]
    }
  ]
})

export default router

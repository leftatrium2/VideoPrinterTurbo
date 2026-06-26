import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/add_task',
      children: [
        {
          path: 'add_task',
          component: () => import('@/views/AddTask.vue'),
          meta: { breadcrumb: ['breadcrumb.addTask', 'breadcrumb.addTaskNew'] },
        },
        {
          path: 'tasks',
          component: () => import('@/views/TaskList.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.taskList'] },
        },
        {
          path: 'settings/asr',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.asr'] },
        },
        {
          path: 'settings/llm',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.llm'] },
        },
        {
          path: 'settings/material',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.material'] },
        },
        {
          path: 'settings/publish_config',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.publishConfig'] },
        },
        {
          path: 'settings/tts_config',
          component: () => import('@/views/TtsConfig.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.ttsConfig'] },
        },
        {
          path: 'settings/proxy',
          component: () => import('@/components/PlaceholderPage.vue'),
          meta: { breadcrumb: ['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.proxy'] },
        },
      ],
    },
  ],
})

export default router

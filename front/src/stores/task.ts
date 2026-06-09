import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTasks, type Task } from '../services/api'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const total = ref(0)
  const loading = ref(false)
  const page = ref(1)
  const pageSize = ref(20)
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  async function fetchTasks() {
    loading.value = true
    try {
      const result = await getTasks(page.value, pageSize.value)
      tasks.value = result.tasks
      total.value = result.total
    } finally {
      loading.value = false
    }
  }

  function startPolling() {
    if (pollingTimer !== null) return
    pollingTimer = setInterval(() => {
      if (tasks.value.some(t => t.state === 4)) {
        fetchTasks()
      }
    }, 5000)
  }

  function stopPolling() {
    if (pollingTimer !== null) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  return { tasks, total, loading, page, pageSize, fetchTasks, startPolling, stopPolling }
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import * as api from '../services/api'

vi.mock('../services/api')

describe('task store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('fetchTasks 更新 tasks 和 total', async () => {
    const mockTasks = [{ task_id: 'abc', state: 1, progress: 100, logs: [], videos: [] }]
    vi.mocked(api.getTasks).mockResolvedValue({ tasks: mockTasks, total: 1 })

    const { useTaskStore } = await import('./task')
    const store = useTaskStore()
    await store.fetchTasks()

    expect(store.tasks).toEqual(mockTasks)
    expect(store.total).toBe(1)
    expect(store.loading).toBe(false)
  })

  it('fetchTasks 期间 loading 为 true', async () => {
    let resolve!: (v: any) => void
    vi.mocked(api.getTasks).mockReturnValue(new Promise(r => { resolve = r }))

    const { useTaskStore } = await import('./task')
    const store = useTaskStore()
    const p = store.fetchTasks()
    expect(store.loading).toBe(true)
    resolve({ tasks: [], total: 0 })
    await p
    expect(store.loading).toBe(false)
  })

  it('stopPolling 清除定时器', async () => {
    vi.mocked(api.getTasks).mockResolvedValue({ tasks: [], total: 0 })
    const { useTaskStore } = await import('./task')
    const store = useTaskStore()
    store.startPolling()
    store.stopPolling()
  })
})

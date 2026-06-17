import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios')

describe('api service', () => {
  let api: typeof import('./api')
  let mockedAxios: any

  beforeEach(async () => {
    vi.resetModules()
    mockedAxios = (await import('axios')).default
    api = await import('./api')
  })

  it('getTasks 调用正确端点', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({
      data: { tasks: [], total: 0 }
    })
    const result = await api.getTasks(1, 10)
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/tasks/', { params: { page: 1, page_size: 10 } })
    expect(result).toEqual({ tasks: [], total: 0 })
  })

  it('addTask 调用正确端点', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({
      data: { message: '任务添加成功' }
    })
    const params = { task_url: 'https://youtube.com/watch?v=test' }
    const result = await api.addTask(params)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/tasks/add', params)
    expect(result).toEqual({ message: '任务添加成功' })
  })

  it('请求失败时抛出错误', async () => {
    mockedAxios.get = vi.fn().mockRejectedValue(new Error('Network Error'))
    await expect(api.getTasks(1, 10)).rejects.toThrow('Network Error')
  })

  it('streamUrl 返回正确路径', async () => {
    expect(api.streamUrl('storage/cache_videos/final.mp4')).toBe('/api/stream/storage/cache_videos/final.mp4')
  })
})

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
      data: { status: 200, data: { tasks: [], total: 0 } }
    })
    const result = await api.getTasks(1, 10)
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/tasks', { params: { page: 1, page_size: 10 } })
    expect(result).toEqual({ tasks: [], total: 0 })
  })

  it('postRewrite 调用正确端点', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({
      data: { status: 200, data: { task_id: 'abc123' } }
    })
    const params = { video_url: 'https://youtube.com/watch?v=test' }
    const result = await api.postRewrite(params)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/rewrite', params)
    expect(result).toEqual({ task_id: 'abc123' })
  })

  it('非 200 状态抛出错误', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({
      data: { status: 400, message: 'Bad Request' }
    })
    await expect(api.getTasks(1, 10)).rejects.toThrow('Bad Request')
  })

  it('streamUrl 返回正确路径', async () => {
    expect(api.streamUrl('storage/tasks/abc/final.mp4')).toBe('/api/v1/stream/storage/tasks/abc/final.mp4')
  })
})

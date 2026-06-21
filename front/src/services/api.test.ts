import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockHttp = {
  get: vi.fn(),
  post: vi.fn(),
}

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockHttp),
  },
}))

describe('api service', () => {
  let api: typeof import('./api')

  beforeEach(async () => {
    vi.resetModules()
    mockHttp.get = vi.fn()
    mockHttp.post = vi.fn()
    api = await import('./api')
  })

  it('getTasks 调用正确端点', async () => {
    mockHttp.get.mockResolvedValue({ data: { tasks: [], total: 0 } })
    const result = await api.getTasks(1, 10)
    expect(mockHttp.get).toHaveBeenCalledWith('/tasks/', { params: { page: 1, page_size: 10 } })
    expect(result).toEqual({ tasks: [], total: 0 })
  })

  it('addTask 调用正确端点', async () => {
    mockHttp.post.mockResolvedValue({ data: { message: '任务添加成功' } })
    const params = { task_url: 'https://youtube.com/watch?v=test' }
    const result = await api.addTask(params)
    expect(mockHttp.post).toHaveBeenCalledWith('/tasks/add', params)
    expect(result).toEqual({ message: '任务添加成功' })
  })

  it('请求失败时抛出错误', async () => {
    mockHttp.get.mockRejectedValue(new Error('Network Error'))
    await expect(api.getTasks(1, 10)).rejects.toThrow('Network Error')
  })

  it('streamUrl 返回正确路径', () => {
    expect(api.streamUrl('storage/cache_videos/final.mp4'))
      .toBe('http://localhost:8080/stream/storage/cache_videos/final.mp4')
  })

  it('checkTaskUrl 成功时返回 code 0', async () => {
    mockHttp.get.mockResolvedValue({ data: { code: 0, msg: 'success', data: {} } })
    const result = await api.checkTaskUrl('https://www.youtube.com/shorts/XV2_PfXqAJI')
    expect(mockHttp.get).toHaveBeenCalledWith('/tasks/check', {
      params: { url: 'https://www.youtube.com/shorts/XV2_PfXqAJI' },
    })
    expect(result).toEqual({ code: 0, msg: 'success', data: {} })
  })

  it('checkTaskUrl 失败时返回非 0 code', async () => {
    mockHttp.get.mockResolvedValue({ data: { code: 1101, msg: '任务 url 检查失败', data: {} } })
    const result = await api.checkTaskUrl('bad-url')
    expect(result.code).toBe(1101)
    expect(result.msg).toBe('任务 url 检查失败')
  })

  it('checkTaskUrl 网络异常时抛出错误', async () => {
    mockHttp.get.mockRejectedValue(new Error('Network Error'))
    await expect(api.checkTaskUrl('https://example.com')).rejects.toThrow('Network Error')
  })
})

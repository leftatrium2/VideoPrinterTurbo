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
    mockHttp.get.mockResolvedValue({ data: { code: 0, msg: 'success', data: { data: [], total: 0, page: 1, page_size: 10 } } })
    const result = await api.getTasks(1, 10)
    expect(mockHttp.get).toHaveBeenCalledWith('/tasks/list', { params: { page: 1, page_size: 10 } })
    expect(result).toEqual({ tasks: [], total: 0 })
  })

  it('getTaskDetail 调用正确端点', async () => {
    const detail = {
      task_url: 'https://www.youtube.com/shorts/TT9Gl0gR2jg',
      task_id: '20260701212108501553',
      is_from_asr_or_subtitle: 1,
      audio_rewrite_type: 2,
      is_llm: 1,
      llm_prompt: 'LLM 提示词 (Prompt)',
      is_rewrite_to_tts: 1,
      tts_server: 'TTS_LIST_AZURE_TTS_V1',
      tts_voice: 'zh-CN-XiaoxiaoNeural',
      tts_volume: 1.0,
      tts_speed: 1.0,
      is_rewrite_to_subtitle: 1,
      subtitle_font: 'Charm-Bold.ttf',
      subtitle_position: '',
      subtitle_font_color: 16777215,
      subtitle_border_color: 0,
      subtitle_size: 30,
      is_bgm: 1,
      uploaded_bgm: '{}',
      bgm_volume: 0.5,
      is_video_material: 1,
      video_material_type: 'pexels',
      uploaded_video_material: '[]',
      video_material_splicing_mode: 1,
      video_material_transition_mode: 1,
      video_material_Video_ratio: 1,
      video_material_max_duration: 10,
      video_material_generate_count: 1,
      is_publish: 0,
      status: 0,
      create_time: '2026-07-01 21:21:08',
      is_deleted: 0,
      error_code: 0,
      error_desc: '',
    }
    mockHttp.get.mockResolvedValue({ data: { code: 0, msg: 'success', data: detail } })
    const result = await api.getTaskDetail('20260701212108501553')
    expect(mockHttp.get).toHaveBeenCalledWith('/tasks/get', { params: { task_id: '20260701212108501553' } })
    expect(result).toEqual(detail)
  })

  it('getTaskDetail 失败时抛出错误', async () => {
    mockHttp.get.mockResolvedValue({ data: { code: 1102, msg: '任务不存在', data: {} } })
    await expect(api.getTaskDetail('bad-id')).rejects.toThrow('任务不存在')
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

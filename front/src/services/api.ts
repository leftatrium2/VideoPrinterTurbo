import axios from 'axios'

export interface Task {
  task_id: string
  state: number
  progress: number
  logs: string[]
  videos: string[]
  params?: Record<string, unknown>
}

export interface TaskListResult {
  tasks: Task[]
  total: number
}

export interface RewriteParams {
  video_url: string
  rewrite_instruction?: string
  video_script?: string
  voice_name?: string
  voice_rate?: number
  bgm_type?: string
  bgm_volume?: number
  subtitle_enabled?: boolean
  subtitle_position?: string
  video_aspect?: string
  video_source?: string
  auto_publish?: boolean
  publish_platforms?: string[]
  video_count?: number
  video_clip_duration?: number
  font_size?: number
  n_threads?: number
}

async function request<T>(
  promise: Promise<{ data: { status: number; data?: T; message?: string } }>
): Promise<T> {
  const res = await promise
  if (res.data.status !== 200) {
    throw new Error(res.data.message ?? '请求失败')
  }
  return res.data.data as T
}

export function getTasks(page: number, pageSize: number): Promise<TaskListResult> {
  return request(axios.get('/api/v1/tasks', { params: { page, page_size: pageSize } }))
}

export function getTask(id: string): Promise<Task> {
  return request(axios.get(`/api/v1/tasks/${id}`))
}

export function postRewrite(params: RewriteParams): Promise<{ task_id: string }> {
  return request(axios.post('/api/v1/rewrite', params))
}

export function deleteTask(id: string): Promise<void> {
  return request(axios.delete(`/api/v1/tasks/${id}`))
}

export function stopTask(id: string): Promise<void> {
  return request(axios.post(`/api/v1/tasks/${id}/stop`))
}

export function streamUrl(path: string): string {
  return `/api/v1/stream/${path}`
}

export function downloadUrl(path: string): string {
  return `/api/v1/download/${path}`
}

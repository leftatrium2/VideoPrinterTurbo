import axios from 'axios'

export interface Task {
  id: number
  task_url: string
  create_time: string
  is_deleted: number
  status: number  // 0=pending, 1=running, 2=done, -1=failed
  task_id: number
  error_code: number
  error_desc: string
  local_path?: string
}

export interface TaskListResult {
  tasks: Task[]
  total?: number
}

export interface AddTaskParams {
  task_url: string
  transcription_mode?: string
  llm_enabled?: boolean
  llm_prompt?: string
  output_mode?: string
  tts_service?: string
  tts_voice?: string
  tts_volume?: number
  tts_speed?: number
  subtitle_font?: string
  subtitle_position?: string
  subtitle_position_custom?: string
  subtitle_color?: string
  subtitle_stroke_color?: string
  subtitle_stroke_width?: number
  subtitle_size?: number
  bgm_type?: string
  bgm_volume?: number
  video_source?: string
  video_concat_mode?: string
  video_transition?: string
  video_aspect?: string
  video_fragment_duration?: number
  video_count?: number
}

async function request<T>(promise: Promise<{ data: T }>): Promise<T> {
  const res = await promise
  return res.data
}

export function getTasks(page: number, pageSize: number): Promise<TaskListResult> {
  return request(axios.get('/api/tasks/', { params: { page, page_size: pageSize } }))
}

export function addTask(params: AddTaskParams): Promise<{ message: string }> {
  return request(axios.post('/api/tasks/add', params))
}

export function streamUrl(path: string): string {
  return `/api/stream/${path}`
}

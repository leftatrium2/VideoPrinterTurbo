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

export interface CheckUrlResult {
  code: number
  msg: string
  data: Record<string, unknown>
}

export interface TtsListItem {
  name: string
  value: number
}

export interface TtsVoiceItem {
  DisplayName: string
  Value: string
}

export interface TtsConfigDetail {
  voice: TtsVoiceItem[]
  tts_area: string
  tts_apikey: string
  tts_voice: string
  tts_server: number
}

interface ApiResult<T> {
  code: number
  msg: string
  data: T
}

const baseURL = import.meta.env.VITE_API_BASE_URL
const http = axios.create({ baseURL })

async function request<T>(promise: Promise<{ data: T }>): Promise<T> {
  const res = await promise
  return res.data
}

export function getTasks(page: number, pageSize: number): Promise<TaskListResult> {
  return request(http.get('/tasks/', { params: { page, page_size: pageSize } }))
}

export function addTask(params: AddTaskParams): Promise<{ message: string }> {
  return request(http.post('/tasks/add', params))
}

export function checkTaskUrl(url: string): Promise<CheckUrlResult> {
  return request(http.get('/tasks/check', { params: { url } }))
}

export function streamUrl(path: string): string {
  return `${baseURL}/stream/${path}`
}

export function getTtsList(): Promise<TtsListItem[]> {
  return request(http.get('/tts_config/tts_list'))
}

export interface UpdateTtsConfigParams {
  tts_server: number
  tts_voice: string
  tts_area: string
  tts_apikey: string
}

export async function updateTtsConfig(params: UpdateTtsConfigParams): Promise<void> {
  const res = await request<ApiResult<Record<string, unknown>>>(
    http.post('/tts_config/update', params)
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
}

export async function getTtsConfigDetail(engine: number): Promise<TtsConfigDetail> {
  const res = await request<ApiResult<TtsConfigDetail>>(
    http.get('/tts_config/tts_config_detail', { params: { engine } })
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export async function getTtsVoicePreview(engine: number, voice: string): Promise<{ output: string }> {
  const res = await request<ApiResult<{ output: string }>>(
    http.get('/tts_config/tts_voice_preview', { params: { engine, voice } })
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export function ttsPreviewUrl(filePath: string): string {
  return `${baseURL}/tts_config/preview?file_path=${encodeURIComponent(filePath)}`
}

export interface AsrWhisperModel {
  name: string
  value: number
}

export async function getLocalWhisperList(): Promise<AsrWhisperModel[]> {
  const res = await request<ApiResult<AsrWhisperModel[]>>(
    http.get('/asr_config/local_whisper_list')
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export interface AsrConfigData {
  tencent_cloud_secret_id: string
  tencent_cloud_secret_key: string
  xfyun_appid: string
  xfyun_secret_key: string
  xfyun_web_api: string
  local_whisper_type: number
}

export async function getAsrConfig(): Promise<AsrConfigData> {
  const res = await request<ApiResult<AsrConfigData>>(
    http.get('/asr_config/')
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export async function updateAsrConfig(params: AsrConfigData): Promise<void> {
  const res = await request<ApiResult<Record<string, unknown>>>(
    http.post('/asr_config/update', params)
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
}

export interface LlmConfigData {
  base_url: string
  api_key: string
  provider_name: string
  llm_model_name: string
  memo: string
}

export async function getLlmConfig(): Promise<LlmConfigData> {
  const res = await request<ApiResult<LlmConfigData>>(
    http.get('/llm_config/')
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export async function updateLlmConfig(params: LlmConfigData): Promise<void> {
  const res = await request<ApiResult<Record<string, unknown>>>(
    http.post('/llm_config/update', params)
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
}

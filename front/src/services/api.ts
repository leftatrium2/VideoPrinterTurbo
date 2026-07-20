import axios from 'axios'
import { i18n } from '@/i18n'

export interface Task {
  id: number
  task_url: string
  create_time: string
  is_deleted: number
  status: number  // 0=pending, 1=running, 2=done, -1=failed
  task_id: string
  error_code: number
  error_desc: string
  local_path?: string
}

export interface TaskListResult {
  tasks: Task[]
  total: number
}

interface TaskListApiData {
  data: Task[]
  total: number
  page: number
  page_size: number
}

export interface AddTaskParams {
  task_url: string
  is_download_proxy: boolean
  // 音频转文字
  is_from_asr_or_subtitle: boolean
  audio_rewrite_type: number
  subtitle_lang: number
  // LLM 改写
  is_llm: boolean
  llm_prompt: string
  // 输出到语音
  is_rewrite_to_tts: boolean
  tts_server: string
  tts_voice: string
  tts_volume: number
  tts_speed: number
  // 输出到字幕
  is_rewrite_to_subtitle: boolean
  subtitle_font: string
  subtitle_font_color: number
  subtitle_border_color: number
  subtitle_size: number
  // 背景音乐
  is_bgm: boolean
  uploaded_bgm: Record<string, unknown>
  bgm_volume: number
  // 视频覆盖
  is_video_material: boolean
  video_material_type: string
  uploaded_video_material: string[]
  video_material_splicing_mode: number
  video_material_transition_mode: number
  video_material_Video_ratio: number
  video_material_max_duration: number
  video_material_generate_count: number
  // 发布
  is_publish: boolean
}

export interface CheckUrlResult {
  code: number
  msg: string
  data: Record<string, unknown>
}

export interface TaskConfigAsrItem {
  name: string
  value: number
}

export interface TaskConfigTtsItem {
  name: string
  value: string
  voices: TtsVoiceItem[]
}

export interface TaskConfigOptionItem {
  name: string
  value: string
}

export interface TaskConfigMaterialData {
  source: TaskConfigOptionItem[]
  splicing: { name: string; value: number }[]
  transition: { name: string; value: number }[]
  ratio: { name: string; value: number }[]
}

export interface TaskConfigData {
  asr: TaskConfigAsrItem[]
  tts: TaskConfigTtsItem[]
  subtitle: TaskConfigOptionItem[]
  bgm: TaskConfigOptionItem[]
  material: TaskConfigMaterialData
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

// 请求拦截器：添加 X-I18n 自定义 Header
http.interceptors.request.use((config) => {
  const locale = (i18n.global.locale as unknown as { value: string }).value || 'zh'
  config.headers['X-I18n'] = locale === 'zh' ? 'cn' : 'en'
  return config
})

async function request<T>(promise: Promise<{ data: T }>): Promise<T> {
  const res = await promise
  return res.data
}

export async function getTasks(page: number, pageSize: number): Promise<TaskListResult> {
  const res = await request<ApiResult<TaskListApiData>>(
    http.get('/tasks/list', { params: { page, page_size: pageSize } })
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return { tasks: res.data.data, total: res.data.total }
}

export interface TaskDetail {
  task_url: string
  is_download_proxy: number
  create_time: string
  is_deleted: number
  status: number
  task_id: string
  error_code: number
  error_desc: string
  is_from_asr_or_subtitle: number
  audio_rewrite_type: number
  subtitle_lang: number
  is_llm: number
  llm_prompt: string
  is_rewrite_to_tts: number
  tts_server: string
  tts_voice: string
  tts_volume: number
  tts_speed: number
  is_rewrite_to_subtitle: number
  subtitle_font: string
  subtitle_position: string
  subtitle_font_color: number
  subtitle_border_color: number
  subtitle_size: number
  is_bgm: number
  uploaded_bgm: string
  bgm_volume: number
  is_video_material: number
  video_material_type: string
  uploaded_video_material: string
  video_material_splicing_mode: number
  video_material_transition_mode: number
  video_material_Video_ratio: number
  video_material_max_duration: number
  video_material_generate_count: number
  is_publish: number
}

export async function getTaskDetail(taskId: string): Promise<TaskDetail> {
  const res = await request<ApiResult<TaskDetail>>(
    http.get('/tasks/get', { params: { task_id: taskId } })
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export function addTask(params: AddTaskParams): Promise<ApiResult<Record<string, unknown>>> {
  return request(http.post('/tasks/add', params))
}

export interface UpdateTaskParams extends AddTaskParams {
  task_id: string
}

export function updateTask(params: UpdateTaskParams): Promise<ApiResult<Record<string, unknown>>> {
  return request(http.post('/tasks/update', params))
}

export function checkTaskUrl(url: string): Promise<CheckUrlResult> {
  return request(http.get('/tasks/check', { params: { url } }))
}

export function deleteTask(taskId: string): Promise<ApiResult<Record<string, unknown>>> {
  return request(http.get('/tasks/del', { params: { task_id: taskId } }))
}

export function getAsrLang(asrType: number): Promise<ApiResult<string[]>> {
  return request(http.get('/tasks/get_asr_lang', { params: { asr_type: asrType } }))
}

export async function getTaskConfig(): Promise<TaskConfigData> {
  const res = await request<ApiResult<TaskConfigData>>(
    http.get('/tasks/')
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
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

export const PROXY_TYPE_HTTPS = 1
export const PROXY_TYPE_SOCKS5 = 2

export interface ProxyConfigData {
  proxy_type: number
  proxy_url: string
  proxy_username: string
  proxy_password: string
}

export async function getProxyConfig(): Promise<ProxyConfigData> {
  const res = await request<ApiResult<ProxyConfigData>>(
    http.get('/proxy_config/')
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
  return res.data
}

export async function updateProxyConfig(params: ProxyConfigData): Promise<void> {
  const res = await request<ApiResult<Record<string, unknown>>>(
    http.post('/proxy_config/update', params)
  )
  if (res.code !== 0) {
    throw new Error(res.msg)
  }
}

interface MaterialListData<T> {
  data: T[]
  page: number
  page_size: number
}

export interface MaterialPexelsItem {
  id: number
  pexels_api_key: string
}

export interface MaterialPixabayItem {
  id: number
  pixabay_api_key: string
}

export async function getPexelsList(page: number, pageSize: number): Promise<MaterialListData<MaterialPexelsItem>> {
  const res = await request<ApiResult<MaterialListData<MaterialPexelsItem>>>(
    http.get('/material_config/pexels_list', { params: { page, page_size: pageSize } })
  )
  if (res.code !== 0) throw new Error(res.msg)
  return res.data
}

export async function addPexelsConfig(apiKey: string): Promise<void> {
  const res = await request<ApiResult<null>>(
    http.post('/material_config/add_pexels_config', { pexels_api_key: apiKey })
  )
  if (res.code !== 0) throw new Error(res.msg)
}

export async function delPexelsConfig(id: number): Promise<void> {
  const res = await request<ApiResult<null>>(
    http.get('/material_config/del_pexels_config', { params: { pexels_config_id: id } })
  )
  if (res.code !== 0) throw new Error(res.msg)
}

export async function getPixabayList(page: number, pageSize: number): Promise<MaterialListData<MaterialPixabayItem>> {
  const res = await request<ApiResult<MaterialListData<MaterialPixabayItem>>>(
    http.get('/material_config/pixabay_list', { params: { page, page_size: pageSize } })
  )
  if (res.code !== 0) throw new Error(res.msg)
  return res.data
}

export async function addPixabayConfig(apiKey: string): Promise<void> {
  const res = await request<ApiResult<null>>(
    http.post('/material_config/add_pixabay_config', { pixabay_api_key: apiKey })
  )
  if (res.code !== 0) throw new Error(res.msg)
}

export async function delPixabayConfig(id: number): Promise<void> {
  const res = await request<ApiResult<null>>(
    http.get('/material_config/del_pixabay_config', { params: { pixabay_config_id: id } })
  )
  if (res.code !== 0) throw new Error(res.msg)
}

export interface BgmUploadResult {
  filename: string
  saved_as: string
  size: number
  content_type: string
}

export async function uploadBgm(file: File): Promise<BgmUploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await request<ApiResult<BgmUploadResult>>(
    http.post('/tasks/upload_bgm', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  )
  if (res.code !== 0) throw new Error(res.msg)
  return res.data
}

export interface MaterialUploadItem {
  filename: string
  saved_as: string
  size: number
  content_type: string
}

export async function uploadMaterial(files: File[]): Promise<MaterialUploadItem[]> {
  const form = new FormData()
  for (const f of files) form.append('files', f)
  const res = await request<ApiResult<MaterialUploadItem[]>>(
    http.post('/tasks/upload_material', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  )
  if (res.code !== 0) throw new Error(res.msg)
  return res.data
}

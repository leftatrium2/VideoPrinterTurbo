<template>
  <div class="add-task-page">

    <!-- Section 1: Download Video (no checkbox — always required) -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Download /></el-icon>
          <span class="section-title">{{ t('addTask.downloadVideo') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpDownload')" />
      </div>
      <div class="section-body">
        <div class="field-label">{{ t('addTask.videoUrl') }}</div>
        <el-input v-model="form.task_url" :placeholder="t('addTask.videoUrlPlaceholder')" size="large">
          <template #append>
            <el-button :icon="Link" :loading="checkingLink" @click="handleCheckLink">{{ t('addTask.checkLink') }}</el-button>
          </template>
        </el-input>
      </div>
    </div>

    <!-- Section 2: Audio to Text -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><User /></el-icon>
          <el-checkbox v-model="enabled.transcription" class="section-toggle" />
          <span class="section-title">{{ t('addTask.audioToText') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpTranscription')" />
      </div>
      <div class="section-body">
        <div class="field-label">{{ t('addTask.transcriptionMode') }}</div>
        <el-select v-model="form.transcription_mode" class="full-width">
          <el-option v-for="item in taskConfig.asr" :key="item.value" :label="item.name" :value="item.value" />
        </el-select>
      </div>
    </div>

    <!-- Section 3: LLM Rewrite -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><EditPen /></el-icon>
          <el-checkbox v-model="enabled.llm" class="section-toggle" />
          <span class="section-title">{{ t('addTask.llmRewrite') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpLlm')" />
      </div>
      <div class="section-body">
        <div class="field-label">{{ t('addTask.llmPrompt') }}</div>
        <el-input
          v-model="form.llm_prompt"
          type="textarea"
          :rows="4"
          :placeholder="t('addTask.llmPromptPlaceholder')"
        />
      </div>
    </div>

    <!-- Section 4: Output to Voice -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><User /></el-icon>
          <el-checkbox v-model="enabled.voice_output" class="section-toggle" />
          <span class="section-title">{{ t('addTask.outputToVoice') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpVoice')" />
      </div>
      <div class="section-body">
        <div class="field-label">{{ t('addTask.ttsService') }}</div>
        <el-select v-model="form.tts_service" class="full-width">
          <el-option v-for="item in taskConfig.tts" :key="item.value" :label="item.name" :value="item.value" />
        </el-select>

        <div class="voice-role-row">
          <div class="voice-role-field">
            <div class="field-label">{{ t('addTask.voiceRole') }}</div>
            <el-select v-model="form.tts_voice" class="full-width">
              <el-option v-for="voice in ttsVoices" :key="voice.Value" :label="voice.DisplayName" :value="voice.Value" />
            </el-select>
          </div>
          <el-button class="test-voice-btn" :loading="previewLoading" @click="handleTestVoice">
            <el-icon v-if="!previewLoading"><component :is="isPlaying ? VideoPause : VideoPlay" /></el-icon>
            {{ testVoiceLabel }}
          </el-button>
          <audio
            ref="audioRef"
            :src="previewUrl"
            style="display: none"
            @play="isPlaying = true"
            @pause="isPlaying = false"
            @ended="isPlaying = false"
          />
        </div>

        <div class="sliders-row">
          <div class="slider-group">
            <div class="field-label">{{ t('addTask.speechVolume') }} ({{ form.tts_volume.toFixed(1) }})</div>
            <el-slider v-model="form.tts_volume" :min="1.0" :max="2.0" :step="0.1" />
          </div>
          <div class="slider-group">
            <div class="field-label">{{ t('addTask.speed') }} ({{ form.tts_speed.toFixed(1) }})</div>
            <el-slider v-model="form.tts_speed" :min="1.0" :max="2.0" :step="0.1" />
          </div>
        </div>
      </div>
    </div>

    <!-- Section 5: Output to Subtitle -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Tickets /></el-icon>
          <el-checkbox v-model="enabled.subtitle_output" class="section-toggle" />
          <span class="section-title">{{ t('addTask.outputToSubtitle') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpSubtitle')" />
      </div>
      <div class="section-body">
        <div class="form-grid-2">
          <div>
            <div class="field-label">{{ t('addTask.font') }}</div>
            <el-select v-model="form.subtitle_font" class="full-width">
              <el-option v-for="item in taskConfig.subtitle" :key="item.value" :label="item.name" :value="item.value" />
            </el-select>
          </div>
          <div>
            <div class="field-label">{{ t('addTask.position') }}</div>
            <el-select v-model="form.subtitle_position" class="full-width">
              <el-option :label="t('addTask.bottomCenter')" value="bottom-center" />
              <el-option :label="t('addTask.topCenter')" value="top-center" />
              <el-option :label="t('addTask.middle')" value="center" />
              <el-option :label="t('addTask.customSubtitlePos')" value="custom" />
            </el-select>
          </div>
        </div>

        <div v-if="form.subtitle_position === 'custom'" class="mt-12">
          <div class="field-label">{{ t('addTask.customPosition') }}</div>
          <el-input v-model="form.subtitle_position_custom" style="width: 200px" placeholder="70" />
        </div>

        <div class="color-row mt-12">
          <div class="color-group">
            <div class="field-label">{{ t('addTask.subtitleColor') }}</div>
            <div class="color-field">
              <input type="color" v-model="form.subtitle_color" class="color-swatch" />
              <span class="color-hex">{{ form.subtitle_color }}</span>
            </div>
          </div>
          <div class="color-group">
            <div class="field-label">{{ t('addTask.strokeColor') }}</div>
            <div class="color-field">
              <input type="color" v-model="form.subtitle_stroke_color" class="color-swatch" />
              <span class="color-hex">{{ form.subtitle_stroke_color }}</span>
            </div>
          </div>
        </div>

        <div class="mt-12">
          <div class="field-label">{{ t('addTask.subtitleSize') }}</div>
          <el-slider v-model="form.subtitle_size" :min="30" :max="100" :step="1" show-tooltip />
        </div>
      </div>
    </div>

    <!-- Section 6: Background Music -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Bell /></el-icon>
          <el-checkbox v-model="enabled.bgm" class="section-toggle" />
          <span class="section-title">{{ t('addTask.bgm') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpBgm')" />
      </div>
      <div class="section-body">
        <div class="field-label">{{ t('addTask.bgmLibrary') }}</div>
        <el-select v-model="form.bgm_library" class="full-width">
          <el-option v-for="item in taskConfig.bgm" :key="item.value" :label="item.name" :value="item.value" />
        </el-select>

        <div class="bgm-layout mt-12">
          <div v-if="form.bgm_library === 'custom'" class="bgm-upload">
            <el-upload
              drag
              :auto-upload="false"
              accept="audio/*"
              :on-change="handleBgmFileChange"
              :file-list="bgmFileList"
              :show-file-list="false"
            >
              <el-icon class="upload-icon"><Document /></el-icon>
              <div class="upload-text">{{ t('addTask.uploadAudio') }}</div>
            </el-upload>
            <div v-if="bgmFileList.length > 0" class="bgm-file-item">
              <el-icon class="bgm-file-icon"><Document /></el-icon>
              <span class="bgm-file-name">{{ bgmFileList[0].name }}</span>
              <el-button size="small" :loading="bgmPreviewLoading" @click="handleBgmPreview">
                {{ bgmIsPlaying ? t('addTask.bgmPreviewPause') : t('addTask.bgmPreview') }}
              </el-button>
              <el-icon class="bgm-file-remove" @click="handleBgmRemove"><Close /></el-icon>
            </div>
            <audio ref="bgmPreviewAudioRef" style="display:none" @ended="bgmIsPlaying = false" />
          </div>
          <div class="bgm-volume">
            <div class="field-label">{{ t('addTask.bgmVolume') }}</div>
            <div class="volume-row">
              <span class="vol-icon">🔉</span>
              <el-slider v-model="form.bgm_volume" :min="0" :max="1" :step="0.05" class="vol-slider" />
              <span class="vol-icon">🔊</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 7: Video Overlay -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Film /></el-icon>
          <el-checkbox v-model="enabled.video_overlay" class="section-toggle" />
          <span class="section-title">{{ t('addTask.videoOverlay') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpVideoOverlay')" />
      </div>
      <div class="section-body">
        <div class="form-grid-3">
          <div>
            <div class="field-label">{{ t('addTask.videoSource') }}</div>
            <el-select v-model="form.video_source" class="full-width">
              <el-option v-for="item in taskConfig.material.source" :key="item.value" :label="item.name" :value="item.value" />
            </el-select>
          </div>
          <div>
            <div class="field-label">{{ t('addTask.concatMode') }}</div>
            <el-select v-model="form.video_concat_mode" class="full-width">
              <el-option v-for="item in taskConfig.material.splicing" :key="item.value" :label="item.name" :value="item.value" />
            </el-select>
          </div>
          <div>
            <div class="field-label">{{ t('addTask.transitionMode') }}</div>
            <el-select v-model="form.video_transition" class="full-width">
              <el-option v-for="item in taskConfig.material.transition" :key="item.value" :label="item.name" :value="item.value" />
            </el-select>
          </div>
        </div>

        <div v-if="form.video_source === 'local'" class="upload-zone mt-12">
          <el-upload drag :auto-upload="false" accept="video/*" :on-change="handleVideoFileChange" :file-list="videoFileList" :show-file-list="false" multiple>
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">{{ t('addTask.uploadVideo') }}</div>
            <div class="upload-hint">{{ t('addTask.uploadVideoHint') }}</div>
          </el-upload>
          <div v-for="(file, index) in videoFileList" :key="file.uid" class="bgm-file-item mt-4">
            <el-icon class="bgm-file-icon"><Film /></el-icon>
            <span class="bgm-file-name">{{ file.name }}</span>
            <el-icon class="bgm-file-remove" @click="handleVideoFileRemove(index)"><Close /></el-icon>
          </div>
        </div>

        <div class="form-grid-3 mt-12">
          <div>
            <div class="field-label">{{ t('addTask.videoAspect') }}</div>
            <el-select v-model="form.video_aspect" class="full-width">
              <el-option v-for="item in taskConfig.material.ratio" :key="item.value" :label="item.name" :value="item.value" />
            </el-select>
          </div>
          <div>
            <div class="field-label">{{ t('addTask.maxDuration') }}</div>
            <el-input v-model.number="form.video_fragment_duration" type="number" :min="2" :max="30" class="full-width" />
          </div>
          <div>
            <div class="field-label">{{ t('addTask.videoCount') }}</div>
            <el-input v-model.number="form.video_count" type="number" :min="1" :max="5" class="full-width" />
          </div>
        </div>
      </div>
    </div>

    <!-- Section 8: Publish -->
    <div class="section-card">
      <div class="section-header">
        <div class="header-left">
          <el-icon class="section-icon"><Share /></el-icon>
          <el-checkbox :model-value="false" class="section-toggle" @click="() => ElMessage.warning(t('addTask.publishNotAvailable'))" />
          <span class="section-title">{{ t('addTask.publish') }}</span>
        </div>
        <HelpPopover :content="t('addTask.helpPublish')" />
      </div>
      <div class="section-body">
        <div class="field-label">{{ t('addTask.publishSettings') }}</div>
        <el-input
          type="textarea"
          :rows="5"
          :model-value="publishPlaceholder"
          readonly
          class="publish-textarea"
        />
      </div>
    </div>

    <!-- Submit -->
    <div class="submit-area">
      <el-button type="primary" size="large" :loading="submitting" class="submit-btn" @click="handleSubmit">
        <el-icon><Promotion /></el-icon>
        {{ t('addTask.startTask') }}
      </el-button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { defineComponent, reactive, ref, h, onMounted, watch, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElPopover } from 'element-plus'
import type { UploadFile } from 'element-plus'
import {
  Download, User, EditPen, Tickets, Bell, Film, Share, Promotion,
  QuestionFilled, Upload, Document, Link, VideoPlay, VideoPause, Close,
} from '@element-plus/icons-vue'
import { addTask, checkTaskUrl, getTaskConfig, getTaskDetail, getTtsVoicePreview, ttsPreviewUrl, uploadBgm, uploadMaterial } from '@/services/api'
import type { TaskConfigData, TaskConfigMaterialData, TtsVoiceItem, BgmUploadResult, TaskDetail } from '@/services/api'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

/* -------- inline helper component for help popovers -------- */
const HelpPopover = defineComponent({
  props: { content: { type: String, required: true } },
  setup(props) {
    return () => h(ElPopover, { trigger: 'click', placement: 'bottom-end', width: 320 }, {
      reference: () => h('span', { class: 'help-link' }, [
        h(QuestionFilled, { style: { fontSize: '13px', marginRight: '3px' } }),
        t('addTask.usageGuide'),
      ]),
      default: () => h('p', { style: { lineHeight: '1.7', fontSize: '13px' } }, props.content),
    })
  },
})

/* -------- task config from server -------- */
const taskConfig = reactive<TaskConfigData>({
  asr: [],
  tts: [],
  subtitle: [],
  bgm: [],
  material: { source: [], splicing: [], transition: [], ratio: [] },
})

/* -------- section enable flags -------- */
const enabled = reactive({
  transcription: false,
  llm: false,
  voice_output: false,
  subtitle_output: false,
  bgm: false,
  video_overlay: false,
  publish: false,
})

/* -------- form state -------- */
const form = reactive({
  task_url: '',
  transcription_mode: 0 as number,
  llm_prompt: '',
  tts_service: '',
  tts_voice: '',
  tts_volume: 1.0,
  tts_speed: 1.0,
  subtitle_font: '',
  subtitle_position: 'bottom-center',
  subtitle_position_custom: '70',
  subtitle_color: '#ffffff',
  subtitle_stroke_color: '#000000',
  subtitle_size: 60,
  bgm_library: '',
  bgm_volume: 0.5,
  video_source: '',
  video_concat_mode: 0 as number,
  video_transition: 0 as number,
  video_aspect: 0 as number,
  video_fragment_duration: 10,
  video_count: 1,
})

const TTS_ENGINE_MAP: Record<string, number> = {
  TTS_LIST_AZURE_TTS_V1: 1,
  TTS_LIST_AZURE_TTS_V2: 2,
  TTS_LIST_SILICON_FLOW_TTS: 3,
  TTS_LIST_GOOGLE_GEMINI_TTS: 4,
  TTS_LIST_XIAOMI_MIMO_TTS: 5,
}

const ttsVoices = computed((): TtsVoiceItem[] => {
  const found = taskConfig.tts.find(t => t.value === form.tts_service)
  return found ? found.voices : []
})

const audioRef = ref<HTMLAudioElement | null>(null)
const previewUrl = ref('')
const previewLoading = ref(false)
const isPlaying = ref(false)
const testVoiceLabel = computed(() => {
  if (!previewUrl.value) return t('addTask.testVoice')
  return isPlaying.value ? t('ttsConfig.pause') : t('ttsConfig.play')
})

onMounted(async () => {
  try {
    const config = await getTaskConfig()
    taskConfig.asr = config.asr
    taskConfig.tts = config.tts
    taskConfig.subtitle = config.subtitle
    taskConfig.bgm = config.bgm
    taskConfig.material = config.material
    if (config.asr.length > 0) form.transcription_mode = config.asr[0].value
    if (config.tts.length > 0) {
      form.tts_service = config.tts[0].value
      if (config.tts[0].voices.length > 0) form.tts_voice = config.tts[0].voices[0].Value
    }
    if (config.subtitle.length > 0) form.subtitle_font = config.subtitle[0].value
    if (config.bgm.length > 0) form.bgm_library = config.bgm[0].value
    if (config.material.source.length > 0) form.video_source = config.material.source[0].value
    if (config.material.splicing.length > 0) form.video_concat_mode = config.material.splicing[0].value
    if (config.material.transition.length > 0) form.video_transition = config.material.transition[0].value
    if (config.material.ratio.length > 0) form.video_aspect = config.material.ratio[0].value
  } catch {
    ElMessage.error(t('addTask.loadConfigFailed'))
  }

  const taskId = route.query.task_id
  if (typeof taskId === 'string' && taskId) {
    try {
      const detail = await getTaskDetail(taskId)
      applyTaskDetail(detail)
    } catch {
      ElMessage.error(t('addTask.loadTaskFailed'))
      router.push('/tasks')
    }
  }
})

watch(() => form.tts_service, () => {
  const found = taskConfig.tts.find(t => t.value === form.tts_service)
  form.tts_voice = found && found.voices.length > 0 ? found.voices[0].Value : ''
  previewUrl.value = ''
  isPlaying.value = false
})

watch(() => form.tts_voice, () => {
  previewUrl.value = ''
  isPlaying.value = false
})


const submitting = ref(false)
const checkingLink = ref(false)
const bgmFileList = ref<UploadFile[]>([])
const bgmUploadedData = ref<BgmUploadResult | null>(null)
const bgmPreviewAudioRef = ref<HTMLAudioElement | null>(null)
const bgmPreviewLoading = ref(false)
const bgmIsPlaying = ref(false)
const videoFileList = ref<UploadFile[]>([])
const materialUploadedPaths = ref<string[]>([])

const publishPlaceholder = `{ 'platform': 'douyin', 'auto_publish': true, ... }`

async function handleCheckLink() {
  if (!form.task_url.trim()) { ElMessage.warning(t('addTask.enterUrlFirst')); return }
  checkingLink.value = true
  try {
    const res = await checkTaskUrl(form.task_url)
    if (res.code === 0) {
      ElMessage.success(t('addTask.checkLinkSuccess'))
    } else {
      ElMessage.error(t('addTask.checkLinkFailed', { msg: res.msg, code: res.code }))
    }
  } catch {
    ElMessage.error(t('addTask.checkLinkError'))
  } finally {
    checkingLink.value = false
  }
}

async function handleTestVoice() {
  if (previewUrl.value) {
    const audio = audioRef.value
    if (!audio) return
    if (audio.paused) { audio.play() } else { audio.pause() }
    return
  }
  const engineId = TTS_ENGINE_MAP[form.tts_service]
  if (!engineId || !form.tts_voice) return
  previewLoading.value = true
  try {
    const result = await getTtsVoicePreview(engineId, form.tts_voice)
    previewUrl.value = ttsPreviewUrl(result.output)
    await nextTick()
    audioRef.value?.play()
  } catch {
    ElMessage.error(t('addTask.testVoiceFailed'))
  } finally {
    previewLoading.value = false
  }
}

async function handleBgmFileChange(file: UploadFile) {
  const audio = bgmPreviewAudioRef.value
  if (audio) { audio.pause(); audio.removeAttribute('src') }
  bgmIsPlaying.value = false
  bgmUploadedData.value = null
  bgmFileList.value = [file]
  if (form.bgm_library !== 'custom') return
  const rawFile = file.raw
  if (!rawFile) return
  try {
    bgmUploadedData.value = await uploadBgm(rawFile)
    ElMessage.success(t('addTask.bgmUploadSuccess'))
  } catch {
    ElMessage.error(t('addTask.bgmUploadFailed'))
    bgmFileList.value = []
    bgmUploadedData.value = null
  }
}

async function handleBgmPreview() {
  const audio = bgmPreviewAudioRef.value
  if (!audio) return

  if (bgmIsPlaying.value) {
    audio.pause()
    bgmIsPlaying.value = false
    return
  }

  if (!bgmUploadedData.value?.saved_as) return
  bgmPreviewLoading.value = true
  try {
    audio.src = ttsPreviewUrl(bgmUploadedData.value.saved_as)
    await audio.play()
    bgmIsPlaying.value = true
  } catch {
    ElMessage.error(t('addTask.bgmUploadFailed'))
  } finally {
    bgmPreviewLoading.value = false
  }
}

function handleBgmRemove() {
  const audio = bgmPreviewAudioRef.value
  if (audio) { audio.pause(); audio.removeAttribute('src') }
  bgmFileList.value = []
  bgmUploadedData.value = null
  bgmIsPlaying.value = false
}

async function handleVideoFileChange(file: UploadFile) {
  const rawFile = file.raw
  if (!rawFile) return
  videoFileList.value = [...videoFileList.value, file]
  try {
    const results = await uploadMaterial([rawFile])
    materialUploadedPaths.value = [...materialUploadedPaths.value, results[0].saved_as]
    ElMessage.success(t('addTask.materialUploadSuccess'))
  } catch {
    ElMessage.error(t('addTask.materialUploadFailed'))
    videoFileList.value = videoFileList.value.filter(f => f.uid !== file.uid)
  }
}

function handleVideoFileRemove(index: number) {
  videoFileList.value = videoFileList.value.filter((_, i) => i !== index)
  materialUploadedPaths.value = materialUploadedPaths.value.filter((_, i) => i !== index)
}

function hexToInt(hex: string): number {
  return parseInt(hex.replace('#', ''), 16)
}

function intToHex(n: number): string {
  return '#' + n.toString(16).padStart(6, '0')
}

const SUBTITLE_POSITION_OPTIONS = ['bottom-center', 'top-center', 'center', 'custom']

function applyTaskDetail(detail: TaskDetail) {
  form.task_url = detail.task_url

  enabled.transcription = !!detail.is_from_asr_or_subtitle
  form.transcription_mode = detail.audio_rewrite_type

  enabled.llm = !!detail.is_llm
  form.llm_prompt = detail.llm_prompt

  enabled.voice_output = !!detail.is_rewrite_to_tts
  form.tts_service = detail.tts_server
  form.tts_voice = detail.tts_voice
  form.tts_volume = detail.tts_volume
  form.tts_speed = detail.tts_speed

  enabled.subtitle_output = !!detail.is_rewrite_to_subtitle
  form.subtitle_font = detail.subtitle_font
  if (SUBTITLE_POSITION_OPTIONS.includes(detail.subtitle_position)) {
    form.subtitle_position = detail.subtitle_position
  } else if (detail.subtitle_position) {
    form.subtitle_position = 'custom'
    form.subtitle_position_custom = detail.subtitle_position
  }
  form.subtitle_color = intToHex(detail.subtitle_font_color)
  form.subtitle_stroke_color = intToHex(detail.subtitle_border_color)
  form.subtitle_size = detail.subtitle_size

  enabled.bgm = !!detail.is_bgm
  form.bgm_volume = detail.bgm_volume
  const bgmData = JSON.parse(detail.uploaded_bgm || '{}') as Partial<BgmUploadResult>
  if (bgmData.saved_as) {
    form.bgm_library = 'custom'
    bgmUploadedData.value = bgmData as BgmUploadResult
    bgmFileList.value = [{ name: bgmData.filename ?? bgmData.saved_as, uid: 0 } as UploadFile]
  }

  enabled.video_overlay = !!detail.is_video_material
  form.video_source = detail.video_material_type
  const materialPaths = JSON.parse(detail.uploaded_video_material || '[]') as string[]
  if (materialPaths.length > 0) {
    materialUploadedPaths.value = materialPaths
    videoFileList.value = materialPaths.map((p, index) => ({
      name: p.split('/').pop() ?? p,
      uid: index,
    } as UploadFile))
  }
  form.video_concat_mode = detail.video_material_splicing_mode
  form.video_transition = detail.video_material_transition_mode
  form.video_aspect = detail.video_material_Video_ratio
  form.video_fragment_duration = detail.video_material_max_duration
  form.video_count = detail.video_material_generate_count
}

async function handleSubmit() {
  if (!form.task_url.trim()) { ElMessage.warning(t('addTask.enterUrl')); return }
  try {
    submitting.value = true
    await addTask({
      task_url: form.task_url,
      // 音频转文字
      is_from_asr_or_subtitle: enabled.transcription,
      audio_rewrite_type: form.transcription_mode,
      // LLM 改写
      is_llm: enabled.llm,
      llm_prompt: form.llm_prompt,
      // 输出到语音
      is_rewrite_to_tts: enabled.voice_output,
      tts_server: form.tts_service,
      tts_voice: form.tts_voice,
      tts_volume: form.tts_volume,
      tts_speed: form.tts_speed,
      // 输出到字幕
      is_rewrite_to_subtitle: enabled.subtitle_output,
      subtitle_font: form.subtitle_font,
      subtitle_font_color: hexToInt(form.subtitle_color),
      subtitle_border_color: hexToInt(form.subtitle_stroke_color),
      subtitle_size: form.subtitle_size,
      // 背景音乐
      is_bgm: enabled.bgm,
      uploaded_bgm: (enabled.bgm && form.bgm_library === 'custom' && bgmUploadedData.value)
        ? bgmUploadedData.value as Record<string, unknown>
        : {},
      bgm_volume: form.bgm_volume,
      // 视频覆盖
      is_video_material: enabled.video_overlay,
      video_material_type: form.video_source,
      uploaded_video_material: (enabled.video_overlay && form.video_source === 'local')
        ? materialUploadedPaths.value
        : [],
      video_material_splicing_mode: form.video_concat_mode,
      video_material_transition_mode: form.video_transition,
      video_material_Video_ratio: form.video_aspect,
      video_material_max_duration: form.video_fragment_duration,
      video_material_generate_count: form.video_count,
      // 发布
      is_publish: false,
    })
    ElMessage.success(t('addTask.taskCreated'))
    router.push('/tasks')
  } catch {
    ElMessage.error(t('addTask.createFailed'))
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.add-task-page {
  padding: 20px;
  max-width: 860px;
}

/* ─── Section cards ─── */
.section-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 20px;
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon { font-size: 15px; color: var(--color-primary); }

.section-toggle { margin: 0; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* help popover trigger — applies to inline component render output */
:deep(.help-link) {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.2s;
}
:deep(.help-link:hover) { color: var(--color-primary); }

.section-body { padding: 16px 20px 20px; }

/* ─── Field labels ─── */
.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-regular);
  margin-bottom: 6px;
}

.full-width { width: 100%; }

.mt-12 { margin-top: 12px; }

/* ─── Output to Voice ─── */
.voice-role-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.voice-role-field { flex: 1; }

.test-voice-btn {
  flex-shrink: 0;
  margin-bottom: 0;
}

.sliders-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 14px;
}

.slider-group {}

/* ─── Output to Subtitle ─── */
.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.color-row {
  display: flex;
  gap: 32px;
}

.color-group {}

.color-field {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.color-swatch {
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 2px;
  cursor: pointer;
}

.color-hex {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-family: 'Courier New', monospace;
}

/* ─── Background Music ─── */
.bgm-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.bgm-upload {
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.bgm-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--el-fill-color-light);
  border-top: 1px solid var(--color-border);
  font-size: 13px;
  color: var(--color-text-regular);
}

.bgm-file-icon {
  font-size: 14px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.bgm-file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bgm-file-remove {
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  &:hover { color: var(--el-color-danger); }
}

.bgm-volume {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-top: 4px;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.vol-icon { font-size: 16px; flex-shrink: 0; }
.vol-slider { flex: 1; }

.upload-icon {
  font-size: 36px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.upload-text {
  font-size: 13px;
  color: var(--color-text-regular);
}

/* ─── Video Overlay ─── */
.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.upload-zone {
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* ─── Publish ─── */
.publish-textarea {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* ─── Submit ─── */
.submit-area {
  display: flex;
  justify-content: center;
  padding: 24px 0 48px;
}

.submit-btn {
  min-width: 220px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}

/* ─── Element Plus overrides ─── */
:deep(.el-form-item) { margin-bottom: 0; }
:deep(.el-select) { width: 100%; }
:deep(.el-upload-dragger) { padding: 20px 16px; }
:deep(.el-upload-dragger .el-icon--upload) { margin: 0; }
</style>

<template>
  <div class="tts-config-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('ttsConfig.title') }}</h1>
      <el-popover trigger="click" placement="bottom-start" :width="320">
        <template #reference>
          <span class="help-link">
            <el-icon><QuestionFilled /></el-icon>{{ t('ttsConfig.usageGuide') }}
          </span>
        </template>
        <p class="help-content">{{ t('ttsConfig.helpUsage') }}</p>
      </el-popover>
    </div>

    <div class="config-card">
      <div class="card-body">
        <div class="field-row">
          <div class="field">
            <div class="field-label">{{ t('ttsConfig.ttsServer') }}</div>
            <el-select v-model="form.ttsServer" class="full-width" :loading="loadingList" @change="handleTtsServerChange">
              <el-option
                v-for="item in ttsList"
                :key="item.value"
                :label="item.name"
                :value="item.value"
              />
            </el-select>
            <p class="field-help">{{ t('ttsConfig.ttsServerHelp') }}</p>
          </div>

          <div class="field">
            <div class="field-label">{{ t('ttsConfig.voiceRole') }}</div>
            <div class="voice-row">
              <el-select v-model="form.voice" class="full-width" :loading="loadingVoiceList">
                <el-option
                  v-for="voice in voiceList"
                  :key="voice.Value"
                  :label="voice.DisplayName"
                  :value="voice.Value"
                />
              </el-select>
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
          </div>
        </div>

        <div class="field-row" v-if="showRegion || showApiKey">
          <div class="field" v-if="showRegion">
            <div class="field-label">{{ t('ttsConfig.region') }}</div>
            <el-input v-model="form.region" :placeholder="t('ttsConfig.regionPlaceholder')" />
          </div>
          <div class="field" v-if="showApiKey">
            <div class="field-label">{{ t('ttsConfig.apiKey') }}</div>
            <el-input v-model="form.apiKey" type="password" show-password />
          </div>
        </div>
      </div>

      <div class="card-footer">
        <el-button text @click="handleDiscard">{{ t('ttsConfig.discard') }}</el-button>
        <el-button type="primary" :loading="saveLoading" @click="handleSave">{{ t('ttsConfig.save') }}</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { QuestionFilled, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import {
  getTtsList,
  getTtsConfigDetail,
  updateTtsConfig,
  getTtsVoicePreview,
  ttsPreviewUrl,
  type TtsListItem,
  type TtsVoiceItem,
} from '@/services/api'

const { t } = useI18n()

const TTS_SERVER_AZURE_V1 = 1
const TTS_SERVER_AZURE_V2 = 2

function defaultForm() {
  return {
    ttsServer: undefined as number | undefined,
    voice: '',
    region: '',
    apiKey: '',
  }
}

const form = reactive(defaultForm())
const ttsList = ref<TtsListItem[]>([])
const loadingList = ref(false)
const voiceList = ref<TtsVoiceItem[]>([])
const loadingVoiceList = ref(false)

const saveLoading = ref(false)

const audioRef = ref<HTMLAudioElement | null>(null)
const previewUrl = ref('')
const previewLoading = ref(false)
const isPlaying = ref(false)

// Azure TTS V1 is free and requires no credentials
const showRegion = computed(() => form.ttsServer === TTS_SERVER_AZURE_V2)
const showApiKey = computed(() => form.ttsServer !== undefined && form.ttsServer !== TTS_SERVER_AZURE_V1)
const testVoiceLabel = computed(() => {
  if (!previewUrl.value) return t('ttsConfig.testVoice')
  return isPlaying.value ? t('ttsConfig.pause') : t('ttsConfig.play')
})

// a previously generated preview belongs to the old voice/engine and is no longer valid
watch(() => form.voice, () => {
  previewUrl.value = ''
  isPlaying.value = false
})

async function loadVoiceList(engine: number) {
  loadingVoiceList.value = true
  try {
    const detail = await getTtsConfigDetail(engine)
    voiceList.value = detail.voice
    form.voice = detail.tts_voice || (detail.voice.length > 0 ? detail.voice[0].Value : '')
    form.region = detail.tts_area
    form.apiKey = detail.tts_apikey
  } catch {
    voiceList.value = []
    form.voice = ''
    ElMessage.error(t('ttsConfig.loadVoiceListFailed'))
  } finally {
    loadingVoiceList.value = false
  }
}

function handleTtsServerChange(value: number) {
  loadVoiceList(value)
}

async function loadTtsList() {
  loadingList.value = true
  try {
    ttsList.value = await getTtsList()
    if (ttsList.value.length > 0) {
      form.ttsServer = ttsList.value[0].value
      await loadVoiceList(form.ttsServer)
    }
  } catch {
    ElMessage.error(t('ttsConfig.loadListFailed'))
  } finally {
    loadingList.value = false
  }
}

async function handleTestVoice() {
  if (previewUrl.value) {
    const audio = audioRef.value
    if (!audio) return
    if (audio.paused) {
      audio.play()
    } else {
      audio.pause()
    }
    return
  }
  if (form.ttsServer === undefined || !form.voice) return
  previewLoading.value = true
  try {
    const result = await getTtsVoicePreview(form.ttsServer, form.voice)
    previewUrl.value = ttsPreviewUrl(result.output)
    await nextTick()
    audioRef.value?.play()
  } catch {
    ElMessage.error(t('ttsConfig.testVoiceFailed'))
  } finally {
    previewLoading.value = false
  }
}

async function handleSave() {
  if (form.ttsServer === undefined) return
  saveLoading.value = true
  try {
    await updateTtsConfig({
      tts_server: form.ttsServer,
      tts_voice: form.voice,
      tts_area: form.region,
      tts_apikey: form.apiKey,
    })
    ElMessage.success(t('ttsConfig.saveSuccess'))
  } catch {
    ElMessage.error(t('ttsConfig.saveFailed'))
  } finally {
    saveLoading.value = false
  }
}

function handleDiscard() {
  Object.assign(form, defaultForm())
  previewUrl.value = ''
  isPlaying.value = false
  if (ttsList.value.length > 0) {
    form.ttsServer = ttsList.value[0].value
    loadVoiceList(form.ttsServer)
  }
}

onMounted(loadTtsList)
</script>

<style scoped>
.tts-config-page {
  padding: 20px;
  max-width: 860px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.help-link {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  transition: color 0.2s;
}
.help-link:hover { color: var(--color-primary); }

.help-content {
  line-height: 1.7;
  font-size: 13px;
}

.config-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-body {
  padding: 20px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.field-row + .field-row {
  margin-top: 24px;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.field-help {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 6px 0 0;
}

.full-width { width: 100%; }

.voice-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.test-voice-btn {
  flex-shrink: 0;
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}
</style>

<template>
  <div class="asr-config-page">
    <h1 class="page-title">{{ t('asrConfig.title') }}</h1>
    <div class="config-card">
      <el-tabs v-model="activeTab" class="asr-tabs">

        <el-tab-pane :label="t('asrConfig.whisperTab')" name="whisper">
          <div class="tab-body">
            <div class="field">
              <div class="field-label">{{ t('asrConfig.modelSelect') }}</div>
              <el-select v-model="whisperForm.model" class="field-input" :loading="loadingWhisperList">
                <el-option
                  v-for="m in whisperModelList"
                  :key="m.value"
                  :label="m.name"
                  :value="m.value"
                />
              </el-select>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('asrConfig.tencentTab')" name="tencent">
          <div class="tab-body">
            <div class="field">
              <div class="field-label">secret_id</div>
              <el-input v-model="tencentForm.secretId" class="field-input" :placeholder="t('asrConfig.placeholder')" />
            </div>
            <div class="field">
              <div class="field-label">secret_key</div>
              <el-input v-model="tencentForm.secretKey" class="field-input" type="password" show-password :placeholder="t('asrConfig.placeholder')" />
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('asrConfig.xunfeiTab')" name="xunfei">
          <div class="tab-body">
            <div class="field">
              <div class="field-label">APPID</div>
              <el-input v-model="xunfeiForm.appId" class="field-input" :placeholder="t('asrConfig.placeholder')" />
            </div>
            <div class="field">
              <div class="field-label">SecretKey</div>
              <el-input v-model="xunfeiForm.secretKey" class="field-input" type="password" show-password :placeholder="t('asrConfig.placeholder')" />
            </div>
            <div class="field">
              <div class="field-label">WebAPI</div>
              <el-input v-model="xunfeiForm.webApi" class="field-input" :placeholder="t('asrConfig.placeholder')" />
            </div>
          </div>
        </el-tab-pane>

      </el-tabs>

      <div class="card-footer">
        <el-button @click="handleReset">{{ t('asrConfig.reset') }}</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ t('asrConfig.submit') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getLocalWhisperList, getAsrConfig, updateAsrConfig, type AsrWhisperModel } from '@/services/api'

const { t } = useI18n()

const activeTab = ref('whisper')
const submitLoading = ref(false)

const whisperModelList = ref<AsrWhisperModel[]>([])
const loadingWhisperList = ref(false)

function defaultWhisperForm() { return { model: 0 } }
function defaultTencentForm() { return { secretId: '', secretKey: '' } }
function defaultXunfeiForm()  { return { appId: '', secretKey: '', webApi: '' } }

const whisperForm = reactive(defaultWhisperForm())
const tencentForm = reactive(defaultTencentForm())
const xunfeiForm  = reactive(defaultXunfeiForm())

async function loadInitialData() {
  loadingWhisperList.value = true

  const [listResult, configResult] = await Promise.allSettled([
    getLocalWhisperList(),
    getAsrConfig(),
  ])

  // populate whisper model list
  if (listResult.status === 'fulfilled') {
    whisperModelList.value = listResult.value
  } else {
    ElMessage.error(t('asrConfig.loadModelListFailed'))
  }
  loadingWhisperList.value = false

  // pre-fill forms from saved config
  if (configResult.status === 'fulfilled') {
    const d = configResult.value
    whisperForm.model =
      d.local_whisper_type ||
      (whisperModelList.value.length > 0 ? whisperModelList.value[0].value : 0)
    tencentForm.secretId  = d.tencent_cloud_secret_id  || ''
    tencentForm.secretKey = d.tencent_cloud_secret_key || ''
    xunfeiForm.appId      = d.xfyun_appid              || ''
    xunfeiForm.secretKey  = d.xfyun_secret_key         || ''
    xunfeiForm.webApi     = d.xfyun_web_api            || ''
  } else if (whisperModelList.value.length > 0) {
    // no saved config — default to first model
    whisperForm.model = whisperModelList.value[0].value
  }
}

function handleReset() {
  if (activeTab.value === 'whisper') {
    Object.assign(whisperForm, defaultWhisperForm())
  } else if (activeTab.value === 'tencent') {
    Object.assign(tencentForm, defaultTencentForm())
  } else {
    Object.assign(xunfeiForm, defaultXunfeiForm())
  }
}

async function handleSubmit() {
  submitLoading.value = true
  try {
    await updateAsrConfig({
      local_whisper_type:        whisperForm.model,
      tencent_cloud_secret_id:   tencentForm.secretId,
      tencent_cloud_secret_key:  tencentForm.secretKey,
      xfyun_appid:               xunfeiForm.appId,
      xfyun_secret_key:          xunfeiForm.secretKey,
      xfyun_web_api:             xunfeiForm.webApi,
    })
    ElMessage.success(t('asrConfig.submitSuccess'))
  } catch {
    ElMessage.error(t('asrConfig.submitFailed'))
  } finally {
    submitLoading.value = false
  }
}

onMounted(loadInitialData)
</script>

<style scoped>
.asr-config-page {
  padding: 20px;
  max-width: 860px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 20px;
}

.config-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.asr-tabs :deep(.el-tabs__header) {
  padding: 0 20px;
  margin-bottom: 0;
}

.tab-body {
  padding: 28px 40px 12px;
}

.field {
  margin-bottom: 20px;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.field-input {
  width: 520px;
  max-width: 100%;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 20px 20px;
  border-top: 1px solid var(--color-border);
}
</style>

<template>
  <div class="batch-download-page">
    <h1 class="page-title">{{ t('batchDownload.title') }}</h1>
    <div class="config-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('batchDownload.linksTab')" name="links">
          <div class="tab-body">
            <label for="batch-download-urls" class="field-label">{{ t('batchDownload.urls') }}</label>
            <el-input
              id="batch-download-urls"
              v-model="urlText"
              type="textarea"
              :rows="12"
              :disabled="submitting"
              :placeholder="t('batchDownload.linksHint')"
            />
            <p class="field-hint">{{ t('batchDownload.linksHint') }}</p>
            <el-checkbox v-model="textUseProxy" :disabled="submitting">{{ t('batchDownload.useProxy') }}</el-checkbox>
            <div class="form-actions">
              <el-button :disabled="submitting" @click="resetText">{{ t('batchDownload.reset') }}</el-button>
              <el-button type="primary" :loading="submitting" @click="submitText">{{ t('batchDownload.submit') }}</el-button>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane :label="t('batchDownload.fileTab')" name="file">
          <div class="tab-body">
            <el-upload
              ref="uploadRef"
              drag
              accept=".txt,.csv"
              :auto-upload="false"
              :show-file-list="false"
              :disabled="submitting"
              :on-change="handleFileChange"
            >
              <el-icon class="upload-icon"><Upload /></el-icon>
              <div>{{ t('batchDownload.chooseFile') }}</div>
              <div class="field-hint">{{ t('batchDownload.fileHint') }}</div>
            </el-upload>
            <div v-if="selectedFile" class="selected-file">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ selectedFile.name }}</span>
              <el-button size="small" :disabled="submitting" @click="clearFile">{{ t('batchDownload.removeFile') }}</el-button>
            </div>
            <p class="field-hint">{{ t('batchDownload.fileContentHint') }}</p>
            <el-checkbox v-model="fileUseProxy" :disabled="submitting">{{ t('batchDownload.useProxy') }}</el-checkbox>
            <div class="form-actions">
              <el-button :disabled="submitting" @click="resetFile">{{ t('batchDownload.reset') }}</el-button>
              <el-button type="primary" :loading="submitting" @click="submitFile">{{ t('batchDownload.submit') }}</el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, type UploadFile, type UploadInstance } from 'element-plus'
import { Upload, Document } from '@element-plus/icons-vue'
import { batchDownload, batchDownloadUpload } from '@/services/api'
import { validateDownloadFile, validateDownloadUrls } from '@/utils/batchDownload'

const { t } = useI18n()
const activeTab = ref('links')
const urlText = ref('')
const textUseProxy = ref(false)
const fileUseProxy = ref(false)
const selectedFile = ref<File | null>(null)
const uploadRef = ref<UploadInstance>()
const submitting = ref(false)

function resetText() {
  urlText.value = ''
  textUseProxy.value = false
}

function clearFile() {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

function resetFile() {
  clearFile()
  fileUseProxy.value = false
}

function handleFileChange(file: UploadFile) {
  // Keep a single selected raw file; clear the upload component's internal queue.
  uploadRef.value?.clearFiles()
  if (!file.raw) return
  const error = validateDownloadFile(file.raw)
  if (error) {
    ElMessage.error(t(`batchDownload.${error}`))
    return
  }
  selectedFile.value = file.raw
}

function checkedUrls(text: string): string[] | undefined {
  const result = validateDownloadUrls(text)
  if (result.error) {
    ElMessage.error(t(`batchDownload.${result.error}`, { line: result.line }))
    return
  }
  return result.urls
}

function showSubmitError(error: unknown) {
  ElMessage.error(error instanceof Error && error.message ? error.message : t('batchDownload.submitFailed'))
}

async function submitText() {
  if (submitting.value) return
  const urls = checkedUrls(urlText.value)
  if (!urls) return
  submitting.value = true
  try {
    await batchDownload(urls.map(task_url => ({ task_url, is_use_proxy: textUseProxy.value })))
    ElMessage.success(t('batchDownload.submitSuccess'))
    resetText()
  } catch (error) {
    showSubmitError(error)
  } finally {
    submitting.value = false
  }
}

async function submitFile() {
  if (submitting.value) return
  const file = selectedFile.value
  if (!file) {
    ElMessage.error(t('batchDownload.fileRequired'))
    return
  }
  const error = validateDownloadFile(file)
  if (error) {
    ElMessage.error(t(`batchDownload.${error}`))
    return
  }
  submitting.value = true
  try {
    let text: string
    try {
      text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer())
    } catch {
      ElMessage.error(t('batchDownload.fileEncoding'))
      return
    }
    if (!checkedUrls(text)) return
    // Strip a UTF-8 BOM, which the backend's utf-8 decoder would otherwise retain in the first URL.
    const uploadFile = new File([text], file.name, { type: file.type })
    await batchDownloadUpload(uploadFile, fileUseProxy.value)
    ElMessage.success(t('batchDownload.submitSuccess'))
    resetFile()
  } catch (error) {
    showSubmitError(error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.batch-download-page { padding: 24px; }
.page-title { font-size: 20px; font-weight: 600; margin: 0 0 24px; }
.config-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: var(--shadow-card); }
.tab-body { max-width: 800px; padding: 16px 0; }
.field-label { display: block; font-size: 14px; margin-bottom: 12px; }
.field-hint { color: var(--color-text-secondary); font-size: 12px; margin: 12px 0; line-height: 1.6; }
.form-actions { display: flex; gap: 12px; margin-top: 24px; }
.form-actions .el-button { margin-left: 0; }
.upload-icon { font-size: 36px; color: var(--color-primary); margin-bottom: 12px; }
.selected-file { display: flex; align-items: center; gap: 10px; margin-top: 12px; font-size: 13px; }
.file-name { flex: 1; overflow-wrap: anywhere; min-width: 0; }
</style>

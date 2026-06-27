<template>
  <div class="llm-config-page">
    <div class="page-header">
      <h1 class="page-title">{{ t('llmConfig.title') }}</h1>
      <el-popover trigger="click" placement="bottom-start" :width="360">
        <template #reference>
          <span class="help-link">
            <el-icon><QuestionFilled /></el-icon>{{ t('llmConfig.usageGuide') }}
          </span>
        </template>
        <p class="help-content">{{ t('llmConfig.helpUsage') }}</p>
      </el-popover>
    </div>

    <div class="config-card">
      <div class="card-body">

        <div class="form-row">
          <div class="form-label">{{ t('llmConfig.supplierName') }}</div>
          <el-input v-model="form.supplierName" class="form-input" :placeholder="t('llmConfig.placeholder')" />
        </div>

        <div class="form-row">
          <div class="form-label">{{ t('llmConfig.remarks') }}</div>
          <el-input v-model="form.remarks" class="form-input" :placeholder="t('llmConfig.placeholder')" />
        </div>

        <div class="form-row">
          <div class="form-label">{{ t('llmConfig.apiKey') }}</div>
          <el-input
            v-model="form.apiKey"
            class="form-input"
            type="password"
            show-password
            :placeholder="t('llmConfig.placeholder')"
          />
        </div>

        <div class="form-row form-row--top">
          <div class="form-label-wrap">
            <div class="form-label">{{ t('llmConfig.apiEndpoint') }}</div>
            <div class="form-help">{{ t('llmConfig.apiEndpointHelp') }}</div>
          </div>
          <el-input v-model="form.apiEndpoint" class="form-input" :placeholder="t('llmConfig.placeholder')" />
        </div>

        <div class="form-row">
          <div class="form-label">{{ t('llmConfig.modelName') }}</div>
          <el-input v-model="form.modelName" class="form-input" :placeholder="t('llmConfig.placeholder')" />
        </div>

      </div>

      <div class="card-footer">
        <el-button @click="handleReset">{{ t('llmConfig.clear') }}</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ t('llmConfig.submit') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import { getLlmConfig, updateLlmConfig } from '@/services/api'

const { t } = useI18n()

const submitLoading = ref(false)

function defaultForm() {
  return { supplierName: '', remarks: '', apiKey: '', apiEndpoint: '', modelName: '' }
}

const form = reactive(defaultForm())

async function loadConfig() {
  try {
    const data = await getLlmConfig()
    form.supplierName = data.provider_name
    form.remarks      = data.memo
    form.apiKey       = data.api_key
    form.apiEndpoint  = data.base_url
    form.modelName    = data.llm_model_name
  } catch {
    ElMessage.error(t('llmConfig.loadFailed'))
  }
}

function handleReset() {
  Object.assign(form, defaultForm())
}

async function handleSubmit() {
  submitLoading.value = true
  try {
    await updateLlmConfig({
      provider_name:   form.supplierName,
      memo:            form.remarks,
      api_key:         form.apiKey,
      base_url:        form.apiEndpoint,
      llm_model_name:  form.modelName,
    })
    ElMessage.success(t('llmConfig.submitSuccess'))
  } catch {
    ElMessage.error(t('llmConfig.submitFailed'))
  } finally {
    submitLoading.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.llm-config-page {
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
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  transition: color 0.2s;
}

.help-link:hover {
  color: var(--color-primary);
}

.help-content {
  font-size: 14px;
  color: var(--color-text-regular);
  line-height: 1.6;
  margin: 0;
}

.config-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-body {
  padding: 32px 40px 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
}

.form-row--top {
  align-items: start;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-regular);
}

.form-label-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-help {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.form-input {
  width: 100%;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 40px 20px;
  border-top: 1px solid var(--color-border);
}
</style>

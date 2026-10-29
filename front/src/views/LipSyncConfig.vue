<template>
  <div class="lip-sync-config-page">
    <h1 class="page-title">{{ t('lipSyncConfig.title') }}</h1>
    <div v-loading="loading" class="config-card">
      <el-tabs v-model="activeTab" class="lip-sync-tabs">
        <el-tab-pane v-for="provider in providers" :key="provider.field" :name="provider.field" :label="t(provider.label)">
          <div class="tab-body">
            <div class="field">
              <label class="field-label" :for="provider.field">{{ provider.field === 'remote_base_url' ? t('lipSyncConfig.selfHostedUrl') : 'API Key' }}</label>
              <el-input
                :id="provider.field"
                v-model="form[provider.field]"
                class="field-input"
                :type="provider.field === 'remote_base_url' ? 'text' : 'password'"
                :show-password="provider.field !== 'remote_base_url'"
                :disabled="!loaded || submitLoading"
                :placeholder="t(provider.field === 'remote_base_url' ? 'lipSyncConfig.selfHostedUrlPlaceholder' : 'lipSyncConfig.placeholder')"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      <div v-if="loadFailed" class="load-error" role="alert">
        {{ t('lipSyncConfig.loadFailed') }}
        <el-button link type="primary" @click="loadConfig">{{ t('lipSyncConfig.retry') }}</el-button>
      </div>
      <div class="card-footer">
        <el-button :disabled="!loaded || submitLoading" @click="form[activeTab] = ''">{{ t('lipSyncConfig.reset') }}</el-button>
        <el-button type="primary" :disabled="!loaded" :loading="submitLoading" @click="handleSubmit">
          {{ t('lipSyncConfig.submit') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getLipSyncConfig, updateLipSyncConfig, type LipSyncConfigData } from '@/services/api'

const { t } = useI18n()
const providers: { field: keyof LipSyncConfigData; label: string }[] = [
  { field: 'remote_base_url', label: 'lipSyncConfig.selfHostedTab' },
  { field: 'sync_labs_apikey', label: 'lipSyncConfig.syncLabsTab' },
  { field: 'fal_latent_sync_apikey', label: 'lipSyncConfig.falAiTab' },
  { field: 'hey_gen_apikey', label: 'lipSyncConfig.heyGenTab' },
]
const activeTab = ref<keyof LipSyncConfigData>('remote_base_url')
const form = reactive<LipSyncConfigData>({ remote_base_url: '', sync_labs_apikey: '', fal_latent_sync_apikey: '', hey_gen_apikey: '' })
const loading = ref(false)
const loaded = ref(false)
const loadFailed = ref(false)
const submitLoading = ref(false)

async function loadConfig() {
  loading.value = true
  loadFailed.value = false
  try {
    const data = await getLipSyncConfig()
    for (const { field } of providers) form[field] = data[field] ?? ''
    loaded.value = true
  } catch {
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!loaded.value || submitLoading.value) return
  submitLoading.value = true
  try {
    await updateLipSyncConfig({ ...form })
    ElMessage.success(t('lipSyncConfig.submitSuccess'))
  } catch {
    ElMessage.error(t('lipSyncConfig.submitFailed'))
  } finally {
    submitLoading.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.lip-sync-config-page {
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

.lip-sync-tabs :deep(.el-tabs__header) {
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
  display: block;
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
.load-error {
  padding: 0 40px 20px;
  color: var(--color-danger, #f56c6c);
}
</style>

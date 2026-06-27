<template>
  <div class="proxy-config-page">
    <div class="config-card">
      <div class="card-header">
        <span class="card-title">{{ t('proxyConfig.cardTitle') }}</span>
        <el-popover trigger="click" placement="bottom-end" :width="320">
          <template #reference>
            <el-icon class="help-icon"><InfoFilled /></el-icon>
          </template>
          <p class="help-content">{{ t('proxyConfig.helpUsage') }}</p>
        </el-popover>
      </div>

      <div class="card-body">

        <div class="form-row">
          <div class="form-label">{{ t('proxyConfig.proxyType') }}</div>
          <el-select v-model="form.proxyType" class="form-input">
            <el-option :label="t('proxyConfig.typeHttps')" :value="PROXY_TYPE_HTTPS" />
            <el-option :label="t('proxyConfig.typeSocks5')" :value="PROXY_TYPE_SOCKS5" />
          </el-select>
        </div>

        <div class="form-row">
          <div class="form-label">{{ t('proxyConfig.address') }}</div>
          <el-input v-model="form.address" class="form-input" :placeholder="t('proxyConfig.placeholder')" />
        </div>

        <div class="form-row">
          <div class="form-label">{{ t('proxyConfig.username') }}</div>
          <div class="form-two-col">
            <el-input v-model="form.username" :placeholder="t('proxyConfig.placeholder')" />
            <div class="sub-field">
              <span class="sub-label">{{ t('proxyConfig.password') }}</span>
              <el-input
                v-model="form.password"
                type="password"
                show-password
                :placeholder="t('proxyConfig.placeholder')"
              />
            </div>
          </div>
        </div>

      </div>

      <div class="card-footer">
        <el-button @click="handleReset">{{ t('proxyConfig.clear') }}</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ t('proxyConfig.submit') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { getProxyConfig, updateProxyConfig, PROXY_TYPE_HTTPS, PROXY_TYPE_SOCKS5 } from '@/services/api'

const { t } = useI18n()

const submitLoading = ref(false)

function defaultForm() {
  return { proxyType: PROXY_TYPE_HTTPS, address: '', username: '', password: '' }
}

const form = reactive(defaultForm())

async function loadConfig() {
  try {
    const data = await getProxyConfig()
    // PROXY_CONFIG_TYPE_UNKNOWN (0) 容错：回退到 HTTPS
    form.proxyType = (data.proxy_type === PROXY_TYPE_HTTPS || data.proxy_type === PROXY_TYPE_SOCKS5)
      ? data.proxy_type
      : PROXY_TYPE_HTTPS
    form.address  = data.proxy_url
    form.username = data.proxy_username
    form.password = data.proxy_password
  } catch {
    ElMessage.error(t('proxyConfig.loadFailed'))
  }
}

function handleReset() {
  Object.assign(form, defaultForm())
}

async function handleSubmit() {
  submitLoading.value = true
  try {
    await updateProxyConfig({
      proxy_type:     form.proxyType,
      proxy_url:      form.address,
      proxy_username: form.username,
      proxy_password: form.password,
    })
    ElMessage.success(t('proxyConfig.submitSuccess'))
  } catch {
    ElMessage.error(t('proxyConfig.submitFailed'))
  } finally {
    submitLoading.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.proxy-config-page {
  padding: 20px;
  max-width: 860px;
}

.config-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.help-icon {
  font-size: 18px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color 0.2s;
}

.help-icon:hover {
  color: var(--color-primary);
}

.help-content {
  font-size: 14px;
  color: var(--color-text-regular);
  line-height: 1.6;
  margin: 0;
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

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-regular);
}

.form-input {
  width: 100%;
}

.form-two-col {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: center;
  width: 100%;
}

.sub-field {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.sub-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-regular);
  white-space: nowrap;
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

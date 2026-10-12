<template>
  <div class="model-manager">
    <label>{{ t('asrConfig.localModel') }}</label>
    <el-select :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)">
      <el-option v-for="name in ['tiny', 'base', 'small', 'medium', 'large-v3']" :key="name" :label="name" :value="name" />
    </el-select>
    <p>{{ t('asrConfig.modelHint') }}</p>
    <p v-if="selected" role="status">
      {{ t(`asrConfig.${selected.state}`) }} · {{ selected.completed_files }} / {{ selected.total_files }}
    </p>
    <p v-if="selected?.error" role="alert">{{ selected.error }}</p>
    <p v-if="loadError" role="alert">{{ t('asrConfig.modelLoadFailed') }}</p>
    <p v-if="selected" class="model-path">{{ selected.path }}</p>
    <el-button :disabled="busy || selected?.state === 'ready'" :loading="submitting" @click="download">
      {{ t('asrConfig.modelDownload') }}
    </el-button>
    <el-button @click="refresh">{{ t('asrConfig.modelReload') }}</el-button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { downloadLocalModel, getLocalModelList, type LocalWhisperModelStatus } from '@/services/api'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const { t } = useI18n()
const models = ref<LocalWhisperModelStatus[]>([])
const selected = computed(() => models.value.find(m => m.model === props.modelValue))
const busy = computed(() => ['downloading', 'verifying'].includes(selected.value?.state || ''))
const submitting = ref(false)
const loadError = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
let disposed = false

async function refresh() {
  clearTimeout(timer)
  try {
    models.value = await getLocalModelList()
    loadError.value = false
  } catch {
    loadError.value = true
  } finally {
    if (!disposed && models.value.some(m => ['downloading', 'verifying'].includes(m.state))) {
      timer = setTimeout(refresh, 2000)
    }
  }
}

async function download() {
  submitting.value = true
  try {
    const state = await downloadLocalModel(props.modelValue)
    models.value = [...models.value.filter(m => m.model !== state.model), state]
    await refresh()
  } catch {
    ElMessage.error(t('asrConfig.modelDownloadFailed'))
  } finally {
    submitting.value = false
  }
}

onMounted(refresh)
onUnmounted(() => { disposed = true; clearTimeout(timer) })
</script>

<style scoped>
.model-manager { display: grid; gap: 12px; max-width: 520px; margin-bottom: 20px; }
.model-manager p { margin: 0; color: var(--color-text-secondary); }
.model-path { overflow-wrap: anywhere; font-size: 12px; }
</style>

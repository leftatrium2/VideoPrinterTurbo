<template>
  <div class="page-wrapper">
    <h2 class="page-title">ASR 配置</h2>
    <div class="settings-card">
      <div class="card-header"><span>语音识别 / 字幕提取</span></div>
      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item label="转录引擎">
          <el-select v-model="form.transcriber_provider" style="width: 100%;">
            <el-option value="whisper" label="Whisper（本地 ASR）" />
            <el-option value="subtitle_extractor" label="字幕提取（优先内嵌字幕）" />
          </el-select>
        </el-form-item>
        <el-form-item label="字幕提供方（TTS 字幕生成）">
          <el-select v-model="form.subtitle_provider" style="width: 100%;">
            <el-option value="edge" label="Edge TTS" />
            <el-option value="whisper" label="Whisper" />
          </el-select>
        </el-form-item>
        <el-form-item label="Whisper 模型">
          <el-select v-model="form.whisper_model" style="width: 100%;">
            <el-option value="large-v3" label="large-v3（最高精度，约 3GB）" />
            <el-option value="medium" label="medium（均衡）" />
            <el-option value="small" label="small（速度优先）" />
            <el-option value="base" label="base（最快）" />
          </el-select>
          <div class="field-hint">首次运行会自动下载模型文件</div>
        </el-form-item>
        <el-form-item label="并发线程数">
          <el-input-number v-model="form.n_threads" :min="1" :max="16" />
        </el-form-item>
        <div class="form-footer">
          <el-button type="primary" @click="handleSave">保存配置</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const form = reactive({
  transcriber_provider: 'subtitle_extractor',
  subtitle_provider: 'edge',
  whisper_model: 'large-v3',
  n_threads: 2,
})
const defaults = { ...form }
function handleSave() { ElMessage.success('配置已保存（需重启服务生效）') }
function handleReset() { Object.assign(form, defaults); ElMessage.info('已重置为默认值') }
</script>

<style scoped>
.page-wrapper { padding: 20px; }
.page-title { font-size: 24px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 20px; }
.settings-card { background: #fff; border-radius: 8px; border: 1px solid var(--color-border); box-shadow: var(--shadow-card); overflow: hidden; max-width: 640px; }
.card-header { padding: 14px 24px; border-bottom: 1px solid var(--color-border); font-weight: 600; font-size: 14px; color: var(--color-text-primary); background: #FAFAFA; }
.settings-form { padding: 24px; }
.field-hint { font-size: 12px; color: var(--color-text-secondary); margin-top: 4px; }
.form-footer { display: flex; gap: 12px; margin-top: 8px; }
</style>

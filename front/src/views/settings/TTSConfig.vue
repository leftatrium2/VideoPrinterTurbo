<template>
  <div class="page-wrapper">
    <h2 class="page-title">TTS 配置</h2>
    <div class="settings-card">
      <div class="card-header"><span>文字转语音</span></div>
      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item label="默认语音">
          <el-select v-model="form.voice_name" style="width: 100%;" filterable>
            <el-option-group label="中文">
              <el-option value="zh-CN-XiaoxiaoNeural" label="晓晓（女，普通话）" />
              <el-option value="zh-CN-YunxiNeural" label="云希（男，普通话）" />
              <el-option value="zh-CN-YunjianNeural" label="云健（男，方言）" />
              <el-option value="zh-TW-HsiaoChenNeural" label="曉臻（女，台湾）" />
            </el-option-group>
            <el-option-group label="英文">
              <el-option value="en-US-JennyNeural" label="Jenny（女，美式）" />
              <el-option value="en-US-GuyNeural" label="Guy（男，美式）" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="语速">
          <el-slider v-model="form.voice_rate" :min="0.5" :max="2.0" :step="0.1" show-input style="padding-right: 8px;" />
          <div class="field-hint">1.0 为正常速度，建议范围 0.8 ~ 1.3</div>
        </el-form-item>
        <el-form-item label="背景音乐">
          <el-radio-group v-model="form.bgm_type">
            <el-radio value="random">随机</el-radio>
            <el-radio value="none">无背景音乐</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="背景音量">
          <el-slider v-model="form.bgm_volume" :min="0" :max="1" :step="0.05" show-input style="padding-right: 8px;" />
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
  voice_name: 'zh-CN-XiaoxiaoNeural',
  voice_rate: 1.0,
  bgm_type: 'random',
  bgm_volume: 0.2,
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

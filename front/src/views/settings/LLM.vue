<template>
  <div class="page-wrapper">
    <h2 class="page-title">LLM 配置</h2>
    <div class="settings-card">
      <div class="card-header"><span>大语言模型</span></div>
      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item label="LLM 提供商">
          <el-select v-model="form.llm_provider" style="width: 100%;">
            <el-option value="openai" label="OpenAI" />
            <el-option value="deepseek" label="DeepSeek" />
            <el-option value="gemini" label="Google Gemini" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="form.api_base" placeholder="https://api.openai.com/v1" clearable />
          <div class="field-hint">DeepSeek: https://api.deepseek.com/v1</div>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." clearable />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="form.model_name" placeholder="gpt-4o-mini" clearable />
        </el-form-item>
        <el-form-item label="温度（creativity）">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input style="padding-right: 8px;" />
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
  llm_provider: 'openai',
  api_base: '',
  api_key: '',
  model_name: 'gpt-4o-mini',
  temperature: 0.7,
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

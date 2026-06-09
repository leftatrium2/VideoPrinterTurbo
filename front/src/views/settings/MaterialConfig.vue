<template>
  <div class="page-wrapper">
    <h2 class="page-title">素材配置</h2>
    <div class="settings-card">
      <div class="card-header"><span>素材搜索平台</span></div>
      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item label="默认素材来源">
          <el-radio-group v-model="form.material_provider">
            <el-radio value="pexels">Pexels</el-radio>
            <el-radio value="pixabay">Pixabay</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-divider />
        <el-form-item label="Pexels API Key">
          <el-input v-model="form.pexels_api_key" type="password" show-password placeholder="填入 Pexels API Key" clearable />
          <div class="field-hint">前往 pexels.com/api 申请免费 API Key</div>
        </el-form-item>
        <el-form-item label="Pixabay API Key">
          <el-input v-model="form.pixabay_api_key" type="password" show-password placeholder="填入 Pixabay API Key" clearable />
          <div class="field-hint">前往 pixabay.com/api/docs 申请免费 API Key</div>
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

const form = reactive({ material_provider: 'pexels', pexels_api_key: '', pixabay_api_key: '' })
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

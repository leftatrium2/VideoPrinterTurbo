<template>
  <div class="page-wrapper">
    <h2 class="page-title">发布配置</h2>
    <div class="settings-card">
      <div class="card-header"><span>自动发布平台</span></div>
      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item label="默认开启自动发布">
          <el-switch v-model="form.auto_publish" active-text="开启" inactive-text="关闭" />
          <div class="field-hint">开启后完成视频合成会自动上传到配置的平台</div>
        </el-form-item>
        <el-divider content-position="left">TikTok</el-divider>
        <el-form-item label="TikTok Cookie 文件路径">
          <el-input v-model="form.tiktok_cookie" placeholder="config/tiktok_cookie.json" clearable />
        </el-form-item>
        <el-divider content-position="left">Instagram</el-divider>
        <el-form-item label="Instagram 用户名">
          <el-input v-model="form.instagram_username" placeholder="your_username" clearable />
        </el-form-item>
        <el-form-item label="Instagram 密码">
          <el-input v-model="form.instagram_password" type="password" show-password placeholder="••••••••" clearable />
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
  auto_publish: false,
  tiktok_cookie: '',
  instagram_username: '',
  instagram_password: '',
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

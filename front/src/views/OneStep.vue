<template>
  <div class="page-wrapper">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">一步完成</h2>
        <p class="page-subtitle">高效完成您的自动化任务流</p>
      </div>
      <el-button :icon="List" @click="drawerOpen = true">任务列表</el-button>
    </div>

    <!-- 居中表单卡片 -->
    <div class="form-card">
        <div class="card-header">
          <el-icon class="card-header-icon"><Tickets /></el-icon>
          <span class="card-header-title">输入</span>
        </div>

        <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
          <el-form-item label="视频链接">
            <el-input
              v-model="form.video_url"
              placeholder="https://www.youtube.com/watch?v=... 或 https://www.bilibili.com/video/..."
              clearable
            />
          </el-form-item>

          <el-form-item label="改写指令">
            <el-input
              v-model="form.rewrite_instruction"
              type="textarea"
              :rows="3"
              placeholder="例如：把这段视频的解说词改成英文，风格更活泼，适合短视频传播"
            />
          </el-form-item>

          <el-form-item label="自定义文案（可选，留空到 AI 自动改写）">
            <el-input
              v-model="form.video_script"
              type="textarea"
              :rows="4"
              placeholder="如果留空，AI 会根据视频字幕和改写指令自动生成新文案"
            />
          </el-form-item>

          <el-button
            native-type="submit"
            :loading="submitting"
            class="submit-btn"
            size="large"
          >
            <el-icon v-if="!submitting"><Promotion /></el-icon>
            开始改写
          </el-button>
        </el-form>
      </div>

    <!-- 任务列表 Drawer -->
    <el-drawer
      v-model="drawerOpen"
      title="任务列表"
      direction="rtl"
      size="420px"
    >
      <div class="drawer-toolbar">
        <el-button size="small" :loading="store.loading" @click="store.fetchTasks()">刷新</el-button>
      </div>

      <div v-if="store.tasks.length === 0 && !store.loading" class="empty-tip">
        暂无任务，提交后将在此显示
      </div>

      <div v-for="task in store.tasks" :key="task.task_id" class="task-item">
        <div class="task-row">
          <div class="task-left">
            <el-tag :type="stateTagType(task.state)" size="small">{{ stateLabel(task.state) }}</el-tag>
            <span class="task-id">{{ task.task_id.slice(0, 8) }}…</span>
          </div>
          <div class="task-actions">
            <el-button size="small" type="danger" plain :disabled="task.state !== 4" @click="handleStop(task.task_id)">停止</el-button>
            <el-button size="small" @click="handleEdit(task)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(task.task_id)">删除</el-button>
          </div>
        </div>

        <el-progress v-if="task.state === 4" :percentage="task.progress" :stroke-width="4" style="margin-top: 8px;" />

        <el-collapse v-if="task.logs?.length" style="margin-top: 8px;">
          <el-collapse-item :title="`日志 (${task.logs.length} 条)`">
            <pre class="log-block">{{ task.logs.join('\n') }}</pre>
          </el-collapse-item>
        </el-collapse>

        <div v-if="task.videos?.length" class="video-list">
          <a v-for="v in task.videos" :key="v" :href="v" target="_blank" class="video-link">
            {{ v.split('/').pop() }}
          </a>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { List, Tickets, Promotion } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { postRewrite, stopTask, deleteTask, type RewriteParams, type Task } from '@/services/api'

const store = useTaskStore()
const route = useRoute()
const submitting = ref(false)
const drawerOpen = ref(false)

const form = ref<RewriteParams>({
  video_url: '',
  rewrite_instruction: '',
  video_script: '',
  voice_name: 'zh-CN-XiaoxiaoNeural-Female',
  voice_rate: 1.0,
  bgm_type: 'random',
  bgm_volume: 0.2,
  subtitle_enabled: true,
  subtitle_position: 'bottom',
  video_aspect: '9:16',
  video_source: 'pexels',
  auto_publish: false,
  video_count: 1,
  video_clip_duration: 5,
  font_size: 60,
  n_threads: 2,
})

function stateLabel(state: number): string {
  return state === 1 ? '完成' : state === 4 ? '进行中' : state === -1 ? '失败' : '未知'
}

function stateTagType(state: number): 'success' | 'warning' | 'danger' | 'info' {
  return state === 1 ? 'success' : state === 4 ? 'warning' : state === -1 ? 'danger' : 'info'
}

async function handleSubmit() {
  if (!form.value.video_url) { ElMessage.error('请输入视频链接'); return }
  submitting.value = true
  try {
    const result = await postRewrite(form.value)
    ElMessage.success(`任务已提交: ${result.task_id.slice(0, 8)}…`)
    await store.fetchTasks()
    store.startPolling()
    drawerOpen.value = true
  } catch (e: any) {
    ElMessage.error(e.message ?? '提交失败')
  } finally {
    submitting.value = false
  }
}

async function handleStop(taskId: string) {
  try {
    await stopTask(taskId)
    ElMessage.success('已发送停止请求')
    await store.fetchTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function handleDelete(taskId: string) {
  await ElMessageBox.confirm('确认删除该任务？', '删除确认', { type: 'warning' })
  try {
    await deleteTask(taskId)
    ElMessage.success('任务已删除')
    await store.fetchTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

function handleEdit(task: Task) {
  if (task.params) {
    Object.assign(form.value, task.params)
    drawerOpen.value = false
    ElMessage.info('已将参数回填到表单')
  }
}

onMounted(async () => {
  if (route.query.video_url) {
    form.value.video_url = route.query.video_url as string
  }
  await store.fetchTasks()
  store.startPolling()
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<style scoped>
.page-wrapper { padding: 20px; }

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 32px;
}
.page-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); }
.page-subtitle { font-size: 14px; color: var(--color-text-secondary); margin-top: 4px; }

/* 居中卡片 */
.form-card {
  max-width: 90%;
  margin: 0 auto;
  background: #fff; border-radius: 8px;
  border: 1px solid var(--color-border); box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-header {
  display: flex; align-items: center; gap: 8px;
  padding: 16px 24px; border-bottom: 1px solid var(--color-border);
  background: #fff;
}
.card-header-icon { font-size: 16px; color: var(--color-primary); }
.card-header-title { font-size: 15px; font-weight: 600; color: var(--color-text-primary); }

:deep(.el-form) { padding: 24px; }
:deep(.el-form-item) { margin-bottom: 20px; }
:deep(.el-form-item__label) {
  font-size: 14px; font-weight: 500; color: var(--color-text-primary);
  padding-bottom: 6px;
}

.submit-btn {
  width: 100%; margin-top: 8px;
  background: #F87171; border-color: #F87171; color: #fff;
  font-size: 15px; font-weight: 500;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.submit-btn:hover { background: #EF4444; border-color: #EF4444; }
.submit-btn:active { background: #DC2626; border-color: #DC2626; }

/* Drawer */
.drawer-toolbar {
  display: flex; justify-content: flex-end;
  margin-bottom: 16px;
}

.empty-tip { text-align: center; color: var(--color-text-secondary); padding: 40px 0; font-size: 14px; }

.task-item { padding: 12px 0; border-bottom: 1px solid var(--color-border); }
.task-item:last-child { border-bottom: none; }
.task-row { display: flex; justify-content: space-between; align-items: center; }
.task-left { display: flex; align-items: center; gap: 8px; }
.task-id { font-size: 13px; color: var(--color-text-secondary); font-family: monospace; }
.task-actions { display: flex; gap: 4px; }

.log-block {
  font-size: 12px; font-family: monospace;
  background: #f5f5f5; border-radius: 4px; padding: 8px;
  white-space: pre-wrap; word-break: break-all;
  max-height: 200px; overflow-y: auto;
}

.video-list { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px; }
.video-link { font-size: 13px; color: var(--color-primary); text-decoration: none; }
.video-link:hover { text-decoration: underline; }
</style>

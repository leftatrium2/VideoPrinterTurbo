<template>
  <div class="page-wrapper">
    <div class="page-header">
      <div>
        <h2 class="page-title">一步完成</h2>
        <p class="page-subtitle">填写参数后自动执行从下载到发布的完整流程</p>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左栏：表单 -->
      <el-col :span="10">
        <el-card class="form-card">
          <template #header><span class="card-title">任务参数</span></template>

          <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
            <el-form-item label="视频 URL" required>
              <el-input v-model="form.video_url" placeholder="请输入 YouTube / Bilibili 等视频地址" clearable />
            </el-form-item>

            <el-form-item label="改写指令">
              <el-input
                v-model="form.rewrite_instruction"
                type="textarea" :rows="3"
                placeholder="描述你想要的改写风格或重点，留空则使用默认指令"
              />
            </el-form-item>

            <el-form-item label="自定义脚本（可选，留空则 AI 生成）">
              <el-input
                v-model="form.video_script"
                type="textarea" :rows="3"
                placeholder="直接提供解说词，将跳过 LLM 改写步骤"
              />
            </el-form-item>

            <el-collapse v-model="advancedOpen" class="advanced-collapse">
              <el-collapse-item title="高级参数" name="advanced">
                <el-row :gutter="12">
                  <el-col :span="24">
                    <el-form-item label="语音名称">
                      <el-input v-model="form.voice_name" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="语速">
                      <el-slider v-model="form.voice_rate" :min="0.5" :max="2.0" :step="0.1" show-input input-size="small" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="背景音量">
                      <el-slider v-model="form.bgm_volume" :min="0" :max="1" :step="0.1" show-input input-size="small" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="背景音乐">
                      <el-select v-model="form.bgm_type" style="width: 100%">
                        <el-option label="随机" value="random" />
                        <el-option label="无" value="none" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="宽高比">
                      <el-select v-model="form.video_aspect" style="width: 100%">
                        <el-option label="竖屏 9:16" value="9:16" />
                        <el-option label="横屏 16:9" value="16:9" />
                        <el-option label="方形 1:1" value="1:1" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="素材来源">
                      <el-select v-model="form.video_source" style="width: 100%">
                        <el-option label="Pexels" value="pexels" />
                        <el-option label="Pixabay" value="pixabay" />
                        <el-option label="本地" value="local" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="字幕位置">
                      <el-select v-model="form.subtitle_position" style="width: 100%">
                        <el-option label="底部" value="bottom" />
                        <el-option label="顶部" value="top" />
                        <el-option label="居中" value="center" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="字幕">
                      <el-switch v-model="form.subtitle_enabled" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="自动发布">
                      <el-switch v-model="form.auto_publish" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="视频数量">
                      <el-input-number v-model="form.video_count" :min="1" :max="5" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="片段时长 (s)">
                      <el-input-number v-model="form.video_clip_duration" :min="2" :max="15" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="字体大小">
                      <el-input-number v-model="form.font_size" :min="30" :max="120" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="线程数">
                      <el-input-number v-model="form.n_threads" :min="1" :max="8" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-collapse-item>
            </el-collapse>

            <el-button
              type="primary" native-type="submit"
              :loading="submitting"
              style="width: 100%; margin-top: 16px;"
              size="large"
            >开始改写</el-button>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右栏：任务列表 -->
      <el-col :span="14">
        <el-card class="task-card">
          <template #header>
            <div class="task-header">
              <span class="card-title">任务列表</span>
              <el-button size="small" :loading="store.loading" @click="store.fetchTasks()">刷新</el-button>
            </div>
          </template>

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
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTaskStore } from '@/stores/task'
import { postRewrite, stopTask, deleteTask, type RewriteParams, type Task } from '@/services/api'

const store = useTaskStore()
const route = useRoute()
const submitting = ref(false)
const advancedOpen = ref<string[]>([])

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
  if (!form.value.video_url) { ElMessage.error('请输入视频 URL'); return }
  submitting.value = true
  try {
    const result = await postRewrite(form.value)
    ElMessage.success(`任务已提交: ${result.task_id.slice(0, 8)}…`)
    await store.fetchTasks()
    store.startPolling()
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
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); }
.page-subtitle { font-size: 14px; color: var(--color-text-secondary); margin-top: 4px; }
.card-title { font-weight: 600; color: var(--color-text-primary); }
.form-card, .task-card { border-radius: 8px; }
.advanced-collapse { border: none; }
.task-header { display: flex; justify-content: space-between; align-items: center; }
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

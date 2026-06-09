<template>
  <div class="page-wrapper">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">视频列表</h2>
        <p class="page-subtitle">管理和监控您的视频下载任务状态</p>
      </div>
      <el-button type="primary" :icon="Download" @click="showDownloadDialog = true">
        下载视频
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <div class="stat-card">
          <p class="stat-label">总任务数</p>
          <div class="stat-value-row">
            <span class="stat-value">{{ store.total.toLocaleString() }}</span>
            <span class="stat-badge stat-badge--success">+12%</span>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <p class="stat-label">正在下载</p>
          <div class="stat-value-row">
            <span class="stat-value">{{ runningCount }}</span>
            <span v-if="runningCount > 0" class="stat-badge stat-badge--warning">Running</span>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <p class="stat-label">已完成</p>
          <div class="stat-value-row">
            <span class="stat-value">{{ doneCount.toLocaleString() }}</span>
            <span class="stat-badge stat-badge--primary">Success</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主表格 -->
    <div class="table-card">
      <div class="table-header">
        <h3 class="table-title">任务明细</h3>
        <div class="table-tools">
          <el-input
            v-model="searchText"
            placeholder="搜索地址或路径..."
            :prefix-icon="Search"
            style="width: 256px;"
            clearable
          />
          <el-button :icon="Filter" />
        </div>
      </div>

      <el-table :data="filteredTasks" style="width: 100%">
        <el-table-column label="地址" min-width="300">
          <template #default="{ row }">
            <div class="url-cell">
              <el-icon class="url-icon"><Link /></el-icon>
              <el-link :href="row.params?.video_url" target="_blank" type="primary" class="url-text">
                {{ row.params?.video_url ?? '—' }}
              </el-link>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="本地路径" min-width="200">
          <template #default="{ row }">
            <el-tag v-if="row.videos?.[0]" type="info" class="path-tag">
              {{ row.videos[0] }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="160">
          <template #default="{ row }">
            <span v-if="row.state === 1" class="state-text">完成</span>
            <span v-else-if="row.state === -1" class="state-text state-text--danger">失败，查看日志</span>
            <div v-else-if="row.state === 4">
              <el-progress :percentage="row.progress" :stroke-width="4" />
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" align="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <template v-if="row.state === 1">
                <el-button size="small" type="primary" plain @click="handlePlay(row)">播放</el-button>
                <el-button size="small" type="primary" plain @click="goNextStep()">下一步</el-button>
                <el-button size="small" type="primary" @click="goOneStep(row)">一步完成</el-button>
              </template>
              <template v-else-if="row.state === -1">
                <el-button size="small" type="primary" plain @click="handleRetry(row)">重试</el-button>
                <el-button size="small" type="primary" plain @click="goNextStep()">下一步</el-button>
                <el-button size="small" type="primary" @click="goOneStep(row)">一步完成</el-button>
              </template>
              <template v-else>
                <el-button size="small" disabled>处理中</el-button>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-bar">
        <span class="pagination-info">
          显示 {{ paginationStart }} 到 {{ paginationEnd }} 项，共 {{ store.total }} 项
        </span>
        <el-pagination
          v-model:current-page="store.page"
          v-model:page-size="store.pageSize"
          :total="store.total"
          layout="prev, pager, next"
          background
          @change="store.fetchTasks()"
        />
      </div>
    </div>

    <!-- 视频播放对话框 -->
    <el-dialog v-model="showVideoDialog" title="视频播放" width="720px" destroy-on-close>
      <video v-if="playingSrc" :src="playingSrc" controls style="width: 100%; border-radius: 4px;" />
    </el-dialog>

    <!-- 下载视频对话框 -->
    <el-dialog v-model="showDownloadDialog" title="下载视频" width="480px">
      <el-form @submit.prevent="handleDownload">
        <el-form-item label="视频 URL" required>
          <el-input v-model="newDownloadUrl" placeholder="请输入视频地址" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDownloadDialog = false">取消</el-button>
        <el-button type="primary" :loading="downloading" @click="handleDownload">开始下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, Search, Filter, Link } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { postRewrite, streamUrl, type Task } from '@/services/api'

const store = useTaskStore()
const router = useRouter()

const searchText = ref('')
const showVideoDialog = ref(false)
const showDownloadDialog = ref(false)
const playingSrc = ref('')
const newDownloadUrl = ref('')
const downloading = ref(false)

const runningCount = computed(() => store.tasks.filter(t => t.state === 4).length)
const doneCount = computed(() => store.tasks.filter(t => t.state === 1).length)

const filteredTasks = computed(() => {
  const q = searchText.value.toLowerCase()
  if (!q) return store.tasks
  return store.tasks.filter(t => {
    const url = ((t.params?.video_url as string) ?? '').toLowerCase()
    const path = (t.videos?.[0] ?? '').toLowerCase()
    return url.includes(q) || path.includes(q)
  })
})

const paginationStart = computed(() => store.total === 0 ? 0 : (store.page - 1) * store.pageSize + 1)
const paginationEnd = computed(() => Math.min(store.page * store.pageSize, store.total))

function handlePlay(task: Task) {
  const path = task.videos?.[0]
  if (!path) { ElMessage.warning('暂无视频文件'); return }
  playingSrc.value = streamUrl(path)
  showVideoDialog.value = true
}

function goNextStep() {
  router.push('/steps/doc-extract')
}

function goOneStep(task: Task) {
  const url = task.params?.video_url as string | undefined
  router.push({ path: '/one-step', query: url ? { video_url: url } : {} })
}

async function handleRetry(task: Task) {
  if (!task.params) { ElMessage.warning('无法获取原始参数'); return }
  try {
    const result = await postRewrite(task.params as any)
    ElMessage.success(`重试任务已提交: ${result.task_id.slice(0, 8)}…`)
    await store.fetchTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

async function handleDownload() {
  if (!newDownloadUrl.value) { ElMessage.error('请输入视频地址'); return }
  downloading.value = true
  try {
    const result = await postRewrite({ video_url: newDownloadUrl.value })
    ElMessage.success(`下载任务已提交: ${result.task_id.slice(0, 8)}…`)
    showDownloadDialog.value = false
    newDownloadUrl.value = ''
    await store.fetchTasks()
    store.startPolling()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    downloading.value = false
  }
}

onMounted(async () => {
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

.stats-row { margin-bottom: 16px; }
.stat-card {
  background: #fff; border-radius: 8px; padding: 24px;
  border: 1px solid var(--color-border); box-shadow: var(--shadow-card);
}
.stat-label { font-size: 14px; color: var(--color-text-secondary); font-weight: 500; }
.stat-value-row { display: flex; align-items: baseline; gap: 8px; margin-top: 8px; }
.stat-value { font-size: 30px; font-weight: 700; color: var(--color-text-primary); }
.stat-badge { font-size: 12px; font-weight: 500; }
.stat-badge--success { color: var(--color-success); }
.stat-badge--warning { color: var(--color-warning); }
.stat-badge--primary { color: var(--color-primary); }

.table-card {
  background: #fff; border-radius: 8px;
  border: 1px solid var(--color-border); box-shadow: var(--shadow-card);
  overflow: hidden; margin-bottom: 16px;
}
.table-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-bottom: 1px solid var(--color-border); background: #FAFAFA;
}
.table-title { font-weight: 700; color: var(--color-text-primary); }
.table-tools { display: flex; gap: 8px; }

.url-cell { display: flex; align-items: center; gap: 8px; }
.url-icon { color: var(--color-primary); font-size: 14px; flex-shrink: 0; }
.url-text { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
.path-tag { font-family: monospace; max-width: 180px; overflow: hidden; text-overflow: ellipsis; }

.state-text { font-size: 14px; color: var(--color-text-primary); }
.state-text--danger { color: var(--color-danger); }

.action-buttons { display: flex; justify-content: flex-end; gap: 4px; }

.pagination-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 24px; border-top: 1px solid var(--color-border); background: #FAFAFA;
}
.pagination-info { font-size: 14px; color: var(--color-text-secondary); }
</style>

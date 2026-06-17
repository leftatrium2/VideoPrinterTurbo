<template>
  <div class="task-list-page">

    <!-- Page header bar -->
    <div class="page-header">
      <span class="page-title">{{ t('taskList.title') }}</span>
      <el-button type="primary" :icon="Plus" @click="router.push('/add-task')">
        {{ t('taskList.newTask') }}
      </el-button>
    </div>

    <!-- Table card -->
    <div class="table-card">
      <el-table
        :data="store.tasks"
        v-loading="store.loading"
        style="width: 100%"
        :header-cell-style="{ background: '#FAFAFA', color: '#606266', fontWeight: '500', fontSize: '13px' }"
        :row-style="{ fontSize: '13px' }"
      >
        <!-- Address -->
        <el-table-column :label="t('taskList.address')" min-width="300">
          <template #default="{ row }">
            <div class="address-cell">
              <el-icon :class="['status-dot-icon', statusIconClass(row.status)]">
                <component :is="statusIcon(row.status)" />
              </el-icon>
              <div class="address-info">
                <a :href="row.task_url" target="_blank" class="task-url" :title="row.task_url">
                  {{ truncateUrl(row.task_url) }}
                </a>
                <span class="added-time">Added: {{ formatTime(row.create_time) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- Local path -->
        <el-table-column :label="t('taskList.localPath')" width="280">
          <template #default="{ row }">
            <span v-if="row.local_path" class="local-path">{{ row.local_path }}</span>
            <span v-else class="no-path">{{ t('taskList.noPath') }}</span>
          </template>
        </el-table-column>

        <!-- Status -->
        <el-table-column :label="t('taskList.status')" width="160">
          <template #default="{ row }">
            <div class="status-cell">
              <el-tag :type="statusTagType(row.status)" size="small" class="status-tag">
                <span class="status-dot" :class="statusDotClass(row.status)"></span>
                {{ statusLabel(row.status) }}
              </el-tag>
              <a
                v-if="row.status === -1"
                href="#"
                class="log-link"
                @click.prevent="openLogDialog(row)"
              >{{ t('taskList.viewLogs') }}</a>
            </div>
          </template>
        </el-table-column>

        <!-- Operations -->
        <el-table-column :label="t('taskList.operations')" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.status === 2"
                size="small"
                type="primary"
                plain
                :icon="VideoPlay"
                @click="openPlayDialog(row)"
              >{{ t('taskList.play') }}</el-button>
              <el-button
                v-if="row.status === -1"
                size="small"
                type="warning"
                plain
                :icon="Refresh"
                @click="handleRetry(row)"
              >{{ t('taskList.retry') }}</el-button>
              <el-button
                size="small"
                plain
                :icon="Edit"
                @click="handleEdit(row)"
              >{{ t('taskList.edit') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Footer: count + pagination -->
      <div class="table-footer">
        <span class="entry-count">
          {{ t('taskList.showing', { start: entryStart, end: entryEnd, total: store.total }) }}
        </span>
        <el-pagination
          v-model:current-page="store.page"
          v-model:page-size="store.pageSize"
          :total="store.total"
          layout="prev, pager, next, jumper"
          :pager-count="5"
          background
          @current-change="store.fetchTasks()"
        />
      </div>
    </div>

    <!-- FAB -->
    <button class="fab" @click="router.push('/add-task')" :title="t('taskList.newTask')">
      <el-icon><Plus /></el-icon>
    </button>

    <!-- Video play dialog -->
    <el-dialog v-model="playDialogVisible" :title="t('taskList.videoPlay')" width="800px" destroy-on-close>
      <video
        v-if="selectedTask?.local_path"
        :src="streamUrl(selectedTask.local_path)"
        controls
        autoplay
        style="width: 100%; border-radius: 4px;"
      ></video>
      <p v-else style="text-align:center; color: var(--color-text-secondary);">{{ t('taskList.noVideo') }}</p>
    </el-dialog>

    <!-- Log dialog -->
    <el-dialog v-model="logDialogVisible" :title="t('taskList.errorLog')" width="600px" destroy-on-close>
      <pre class="log-content">{{ selectedTask?.error_desc || t('taskList.noError') }}</pre>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus, VideoPlay, Refresh, Edit, CircleCheckFilled, CircleCloseFilled, Loading, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/task'
import { addTask, streamUrl, type Task } from '@/services/api'

const router = useRouter()
const store = useTaskStore()
const { t } = useI18n()

const playDialogVisible = ref(false)
const logDialogVisible = ref(false)
const selectedTask = ref<Task | null>(null)

onMounted(async () => {
  await store.fetchTasks()
  store.startPolling()
})

onUnmounted(() => {
  store.stopPolling()
})

const entryStart = computed(() => {
  if (store.total === 0) return 0
  return (store.page - 1) * store.pageSize + 1
})
const entryEnd = computed(() => {
  return Math.min(store.page * store.pageSize, store.total)
})

function statusLabel(status: number): string {
  if (status === 2) return t('taskList.statusComplete')
  if (status === 1) return t('taskList.statusInProgress')
  if (status === -1) return t('taskList.statusFailed')
  return t('taskList.statusPending')
}

function statusTagType(status: number): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 2) return 'success'
  if (status === -1) return 'danger'
  if (status === 1) return 'warning'
  return 'info'
}

function statusDotClass(status: number): string {
  if (status === 2) return 'dot-success'
  if (status === -1) return 'dot-danger'
  if (status === 1) return 'dot-warning'
  return 'dot-info'
}

function statusIcon(status: number) {
  if (status === 2) return CircleCheckFilled
  if (status === -1) return CircleCloseFilled
  if (status === 1) return Loading
  return Clock
}

function statusIconClass(status: number): string {
  if (status === 2) return 'icon-success'
  if (status === -1) return 'icon-danger'
  if (status === 1) return 'icon-warning'
  return 'icon-info'
}

function truncateUrl(url: string): string {
  if (url.length <= 50) return url
  return url.slice(0, 47) + '...'
}

function formatTime(t: string): string {
  if (!t) return ''
  return t.replace('T', ' ').slice(0, 16)
}

function openPlayDialog(task: Task) {
  selectedTask.value = task
  playDialogVisible.value = true
}

function openLogDialog(task: Task) {
  selectedTask.value = task
  logDialogVisible.value = true
}

async function handleRetry(task: Task) {
  try {
    await addTask({ task_url: task.task_url })
    ElMessage.success(t('taskList.retrySuccess'))
    store.fetchTasks()
  } catch {
    ElMessage.error(t('taskList.retryFailed'))
  }
}

function handleEdit(task: Task) {
  router.push(`/add-task?video_url=${encodeURIComponent(task.task_url)}`)
}
</script>

<style scoped>
.task-list-page {
  padding: 20px;
  min-height: calc(100vh - var(--topbar-height));
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.table-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* Address column */
.address-cell {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.status-dot-icon {
  font-size: 16px;
  margin-top: 2px;
  flex-shrink: 0;
}
.icon-success { color: var(--color-success); }
.icon-danger  { color: var(--color-danger); }
.icon-warning { color: var(--color-warning); }
.icon-info    { color: var(--color-text-secondary); }

.address-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.task-url {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 13px;
  word-break: break-all;
}
.task-url:hover { text-decoration: underline; }

.added-time {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* Path column */
.local-path {
  font-size: 12px;
  color: var(--color-text-regular);
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.no-path {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-style: italic;
}

/* Status column */
.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.dot-success { background: var(--color-success); }
.dot-danger  { background: var(--color-danger); }
.dot-warning { background: var(--color-warning); }
.dot-info    { background: var(--color-text-secondary); }

.log-link {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
}
.log-link:hover { text-decoration: underline; }

/* Action buttons */
.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* Footer */
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-top: 1px solid var(--color-border);
}

.entry-count {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* FAB */
.fab {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: background 0.2s, transform 0.1s;
  z-index: 100;
}
.fab:hover { background: #66b1ff; }
.fab:active { transform: scale(0.95); }

/* Log dialog */
.log-content {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 16px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  color: var(--color-text-primary);
}
</style>

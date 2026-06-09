<template>
  <div class="page-wrapper">
    <h2 class="page-title">发布</h2>
    <div class="table-card">
      <el-table :data="tableData" style="width: 100%"
        :header-cell-style="{ background: '#FAFAFA', fontWeight: '500', color: '#606266' }">
        <el-table-column label="地址" min-width="220">
          <template #default="{ row }">
            <el-link :href="row.videoUrl" target="_blank" type="primary" class="url-text">{{ row.videoUrl }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="输出视频" min-width="200">
          <template #default="{ row }">
            <span v-if="row.outputVideo" class="path-text">{{ row.outputVideo }}</span>
            <span v-else class="dim-text">暂无输出</span>
          </template>
        </el-table-column>
        <el-table-column label="自动发布" width="100">
          <template #default="{ row }">
            <el-tag :type="row.autoPublish ? 'success' : 'info'" size="small" effect="light">
              {{ row.autoPublish ? '启用' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="tagType(row.state)" size="small" effect="light">{{ stateLabel(row.state) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button v-if="row.outputVideo" size="small" plain type="primary" @click="playVideo(row.outputVideo)">播放</el-button>
              <el-button size="small" type="primary" @click="goOneStep(row)">重新生成</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <span class="total-text">Total {{ store.total }} items</span>
        <el-pagination v-model:current-page="store.page" v-model:page-size="store.pageSize"
          :total="store.total" layout="prev, pager, next" background @change="store.fetchTasks()" />
      </div>
    </div>
    <el-dialog v-model="showVideoDialog" title="视频播放" width="720px" destroy-on-close>
      <video v-if="playingSrc" :src="playingSrc" controls style="width:100%;border-radius:4px;" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import { streamUrl } from '@/services/api'

const store = useTaskStore()
const router = useRouter()
const showVideoDialog = ref(false)
const playingSrc = ref('')

const tableData = computed(() => store.tasks.map(t => ({
  taskId: t.task_id,
  videoUrl: (t.params?.video_url as string) ?? '—',
  outputVideo: t.videos?.[0] ?? '',
  autoPublish: !!(t.params?.auto_publish),
  state: t.state,
})))
function stateLabel(s: number) { return s === 1 ? '已完成' : s === 4 ? '处理中' : s === -1 ? '失败' : '待处理' }
function tagType(s: number): 'success' | 'warning' | 'danger' | 'info' {
  return s === 1 ? 'success' : s === 4 ? 'warning' : s === -1 ? 'danger' : 'info'
}
function playVideo(path: string) { playingSrc.value = streamUrl(path); showVideoDialog.value = true }
function goOneStep(row: { videoUrl: string }) {
  router.push({ path: '/one-step', query: row.videoUrl !== '—' ? { video_url: row.videoUrl } : {} })
}
onMounted(async () => { await store.fetchTasks(); store.startPolling() })
onUnmounted(() => store.stopPolling())
</script>

<style scoped>
.page-wrapper { padding: 20px; }
.page-title { font-size: 24px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 20px; }
.table-card { background: #fff; border-radius: 8px; border: 1px solid var(--color-border); box-shadow: var(--shadow-card); overflow: hidden; }
.url-text { font-size: 13px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
.path-text { font-size: 12px; font-family: monospace; color: var(--color-text-regular); word-break: break-all; }
.dim-text { font-size: 13px; color: var(--color-text-secondary); }
.action-btns { display: flex; justify-content: flex-end; gap: 8px; }
.pagination-bar { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-top: 1px solid var(--color-border); background: #FAFAFA; }
.total-text { font-size: 13px; color: var(--color-text-secondary); }
</style>

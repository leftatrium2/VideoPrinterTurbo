<template>
  <div class="page-wrapper">
    <h2 class="page-title">文档提取</h2>

    <div class="table-card">
      <el-table
        :data="tableData"
        style="width: 100%"
        :header-cell-style="{ background: '#FAFAFA', fontWeight: '500', color: '#606266' }"
      >
        <el-table-column label="地址" min-width="260">
          <template #default="{ row }">
            <el-link
              :href="row.videoUrl"
              target="_blank"
              type="primary"
              class="url-text"
            >{{ row.videoUrl }}</el-link>
          </template>
        </el-table-column>

        <el-table-column label="本地路径" min-width="240">
          <template #default="{ row }">
            <span class="path-text">{{ row.docPath }}</span>
          </template>
        </el-table-column>

        <el-table-column label="文档来源" width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.source === '字幕' ? 'primary' : 'warning'"
              size="small"
              effect="light"
            >{{ row.source }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" align="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button size="small" plain type="primary" @click="goNextStep()">下一步</el-button>
              <el-button size="small" type="primary" @click="goOneStep(row)">一步完成</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <span class="total-text">Total {{ store.total }} items</span>
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '@/stores/task'

const store = useTaskStore()
const router = useRouter()

const tableData = computed(() =>
  store.tasks.map(t => ({
    taskId: t.task_id,
    videoUrl: (t.params?.video_url as string) ?? '—',
    docPath: `storage/cache_documents/${t.task_id.slice(0, 16)}.srt`,
    source: t.task_id.charCodeAt(0) % 2 === 0 ? '字幕' : 'ASR',
    params: t.params,
  }))
)

function goNextStep() {
  router.push('/steps/llm-rewrite')
}

function goOneStep(row: { videoUrl: string }) {
  router.push({
    path: '/one-step',
    query: row.videoUrl !== '—' ? { video_url: row.videoUrl } : {},
  })
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

.page-title {
  font-size: 24px; font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 20px;
}

.table-card {
  background: #fff; border-radius: 8px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.url-text {
  font-size: 13px; max-width: 240px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block;
}

.path-text {
  font-size: 13px; font-family: monospace;
  color: var(--color-text-regular);
  word-break: break-all;
}

.action-btns { display: flex; justify-content: flex-end; gap: 8px; }

.pagination-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-top: 1px solid var(--color-border);
  background: #FAFAFA;
}

.total-text { font-size: 13px; color: var(--color-text-secondary); }
</style>

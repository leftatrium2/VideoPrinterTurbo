<template>
  <div class="material-config-page">
    <h1 class="page-title">{{ t('materialConfig.title') }}</h1>
    <div class="config-card">
      <div class="card-header">
        <el-tabs v-model="activeTab" class="material-tabs" @tab-change="onTabChange">
          <el-tab-pane :label="t('materialConfig.pexelsTab')" name="pexels" />
          <el-tab-pane :label="t('materialConfig.pixabayTab')" name="pixabay" />
        </el-tabs>
        <el-button type="primary" class="add-btn" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          {{ t('materialConfig.addApiKey') }}
        </el-button>
      </div>

      <div class="table-wrapper">
        <el-table :data="currentKeys" v-loading="tableLoading" class="api-table">
          <el-table-column :label="currentColLabel" prop="key" />
          <el-table-column :label="t('materialConfig.operations')" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="handleDelete(row)">
                {{ t('materialConfig.delete') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="currentKeys.length > 0 || currentPage > 1" class="card-footer">
        <el-button :disabled="currentPage === 1" @click="prevPage">
          {{ t('materialConfig.prevPage') }}
        </el-button>
        <span class="page-indicator">
          <strong>{{ currentPage }}</strong>
        </span>
        <el-button :disabled="!hasNextPage" @click="nextPage">
          {{ t('materialConfig.nextPage') }}
        </el-button>
      </div>
    </div>

    <el-dialog
      v-model="showAddDialog"
      :title="t('materialConfig.addApiKey')"
      width="480px"
      @closed="newApiKey = ''"
    >
      <div class="dialog-field">
        <div class="dialog-label">
          {{ t('materialConfig.addDialogLabel', { provider: activeTab === 'pexels' ? 'Pexels' : 'Pixabay' }) }}
        </div>
        <el-input
          v-model="newApiKey"
          :placeholder="t('materialConfig.placeholder')"
          @keyup.enter="handleConfirmAdd"
        />
      </div>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ t('materialConfig.cancel') }}</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleConfirmAdd">
          {{ t('materialConfig.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getPexelsList, addPexelsConfig, delPexelsConfig,
  getPixabayList, addPixabayConfig, delPixabayConfig,
} from '@/services/api'

const { t } = useI18n()

const activeTab = ref('pexels')
const showAddDialog = ref(false)
const currentPage = ref(1)
const pageSize = 10
const tableLoading = ref(false)
const addLoading = ref(false)
const hasNextPage = ref(false)

interface ApiKey {
  id: number
  key: string
}

const currentKeys = ref<ApiKey[]>([])
const newApiKey = ref('')

const currentColLabel = computed(() =>
  activeTab.value === 'pexels'
    ? t('materialConfig.pexelsColLabel')
    : t('materialConfig.pixabayColLabel')
)

async function fetchList() {
  tableLoading.value = true
  try {
    if (activeTab.value === 'pexels') {
      const res = await getPexelsList(currentPage.value, pageSize)
      currentKeys.value = res.data.map(item => ({ id: item.id, key: item.pexels_api_key }))
    } else {
      const res = await getPixabayList(currentPage.value, pageSize)
      currentKeys.value = res.data.map(item => ({ id: item.id, key: item.pixabay_api_key }))
    }
    hasNextPage.value = currentKeys.value.length === pageSize
  } catch {
    ElMessage.error(t('materialConfig.loadFailed'))
  } finally {
    tableLoading.value = false
  }
}

function onTabChange() {
  currentPage.value = 1
  fetchList()
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    fetchList()
  }
}

function nextPage() {
  if (hasNextPage.value) {
    currentPage.value++
    fetchList()
  }
}

async function handleConfirmAdd() {
  if (!newApiKey.value.trim()) {
    ElMessage.warning(t('materialConfig.emptyKeyWarning'))
    return
  }
  addLoading.value = true
  try {
    if (activeTab.value === 'pexels') {
      await addPexelsConfig(newApiKey.value.trim())
    } else {
      await addPixabayConfig(newApiKey.value.trim())
    }
    ElMessage.success(t('materialConfig.addSuccess'))
    showAddDialog.value = false
    await fetchList()
  } catch {
    ElMessage.error(t('materialConfig.addFailed'))
  } finally {
    addLoading.value = false
  }
}

async function handleDelete(row: ApiKey) {
  try {
    await ElMessageBox.confirm(
      t('materialConfig.deleteConfirm'),
      t('materialConfig.confirmTitle'),
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    if (activeTab.value === 'pexels') {
      await delPexelsConfig(row.id)
    } else {
      await delPixabayConfig(row.id)
    }
    ElMessage.success(t('materialConfig.deleteSuccess'))
    if (currentKeys.value.length === 1 && currentPage.value > 1) {
      currentPage.value--
    }
    await fetchList()
  } catch {
    ElMessage.error(t('materialConfig.deleteFailed'))
  }
}

onMounted(fetchList)
</script>

<style scoped>
.material-config-page {
  padding: 20px;
  max-width: 860px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 20px;
}

.config-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  padding-right: 20px;
  border-bottom: 1px solid var(--color-border);
}

.material-tabs {
  flex: 1;
}

.material-tabs :deep(.el-tabs__header) {
  padding: 0 20px;
  margin-bottom: 0;
  border-bottom: none;
}

.add-btn {
  flex-shrink: 0;
}

.table-wrapper {
  padding: 0;
}

.api-table {
  width: 100%;
}

.api-table :deep(.el-table__header-wrapper th) {
  background: #fafafa;
  font-weight: 500;
  color: var(--color-text-primary);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.page-indicator {
  font-size: 14px;
  color: var(--color-text-regular);
  min-width: 48px;
  text-align: center;
}

.page-indicator strong {
  color: var(--color-primary);
}

.dialog-field {
  padding: 4px 0 8px;
}

.dialog-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}
</style>

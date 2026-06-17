<template>
  <div class="layout">
    <AppSidebar />
    <AppTopbar :breadcrumbs="breadcrumbs" />
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const route = useRoute()
const { t } = useI18n()

const breadcrumbs = computed(() =>
  ((route.meta.breadcrumb as string[]) ?? []).map(key => t(key))
)
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }

.content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding-top: var(--topbar-height);
  min-height: 100vh;
  min-width: 0;
}
</style>

<template>
  <div class="resource-detail-page">
    <div class="page-header">
      <h2>资源详情</h2>
      <a-space>
        <a-button @click="$router.push('/resource/recommend')">返回推荐</a-button>
        <a-button @click="$router.push('/resource/library')">返回资源库</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-empty v-if="!resource && !loading" description="资源不存在或无访问权限" />
      <ResourceViewer
        v-else
        :resource="resource"
        @click="recordCurrentEvent('click')"
        @play="recordCurrentEvent('play')"
        @complete="recordCurrentEvent('complete')"
      />
    </a-spin>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute } from 'vue-router'
import { getResource } from '@/api/resource'
import { recordResourceEvent } from '@/api/recommendation'
import ResourceViewer from './components/ResourceViewer.vue'

const route = useRoute()
const loading = ref(false)
const resource = ref(null)

onMounted(() => {
  fetchResource()
})

watch(
  () => route.params.id,
  () => fetchResource()
)

async function fetchResource() {
  const id = Number(route.params.id)
  if (!id) {
    resource.value = null
    return
  }

  loading.value = true
  try {
    resource.value = await getResource(id)
  } catch (e) {
    resource.value = null
    message.error(e.message || '加载资源失败')
  } finally {
    loading.value = false
  }
}

async function recordCurrentEvent(eventType) {
  if (!resource.value?.id) return
  try {
    await recordResourceEvent(resource.value.id, { eventType })
  } catch {
    // ignore
  }
}
</script>

<style scoped>
.resource-detail-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>

<template>
  <div class="page-content resource-page featured-page">
    <section class="featured-shell">
      <div class="featured-topbar">
        <ResourceCommunityTopBar
          active-tab="featured"
          v-model:keyword="query.search"
          v-model:content-type="query.content_type"
          :show-filter="true"
          :searching="loading && !resources.length"
          placeholder="搜索精选标题、简介、作者或标签"
          @search="handleSearch"
          @tab-change="handleTabChange"
        >
          <template #actions>
            <ResourceCommunityUploadEntry />
          </template>
        </ResourceCommunityTopBar>
      </div>

      <div v-if="loading && !resources.length" class="featured-loading">
        <a-spin size="large" />
      </div>

      <a-empty v-else-if="!resources.length" description="暂无精选内容" class="featured-empty" />

      <div v-else class="featured-grid">
        <article
          v-for="item in resources"
          :key="item.id"
          class="featured-card"
          role="link"
          tabindex="0"
          @click="goToDetail(item.id)"
          @keydown.enter.prevent="goToDetail(item.id)"
          @keydown.space.prevent="goToDetail(item.id)"
        >
          <ResourceCardCover
            class="featured-card-cover"
            :title="item.title"
            :content-type="item.content_type"
            :cover-url="item.cover_url"
            minimal
          />
          <h3 class="featured-title">{{ item.title }}</h3>
        </article>
      </div>

      <div ref="loadMoreTriggerRef" class="featured-load-trigger" aria-hidden="true" />

      <div v-if="resources.length" class="featured-footer-state">
        <a-spin v-if="loadingMore" size="small" />
        <span v-else-if="finished">没有更多精选内容了</span>
        <span v-else>继续下滑加载更多</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceListItemResponse } from '@/api/learning-resource'
import { listResources } from '@/api/learning-resource'
import ResourceCardCover from '@/components/resource/ResourceCardCover.vue'
import ResourceCommunityTopBar from '@/components/resource/ResourceCommunityTopBar.vue'
import ResourceCommunityUploadEntry from '@/components/resource/ResourceCommunityUploadEntry.vue'

const PAGE_SIZE = 20

const router = useRouter()

const query = reactive({
  page: 1,
  size: PAGE_SIZE,
  search: '',
  content_type: '',
})

const resources = ref<ResourceListItemResponse[]>([])
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const finished = ref(false)
const loadMoreTriggerRef = ref<HTMLElement | null>(null)

let observer: IntersectionObserver | null = null

onMounted(() => {
  void resetAndFetch()
})

onUnmounted(() => {
  disconnectObserver()
})

watch(loadMoreTriggerRef, (element) => {
  disconnectObserver()
  if (!element) {
    return
  }

  observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      void loadMore()
    }
  }, { rootMargin: '260px 0px' })

  observer.observe(element)
}, { flush: 'post' })

watch(() => query.content_type, (value, previousValue) => {
  if (value === previousValue) {
    return
  }
  void resetAndFetch()
})

function disconnectObserver() {
  observer?.disconnect()
  observer = null
}

async function fetchResources(page: number, reset = false) {
  if (!reset && (loading.value || loadingMore.value || finished.value)) {
    return
  }

  const isFirstPage = reset || page === 1
  if (isFirstPage) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const response = await listResources({
      page,
      size: query.size,
      search: query.search || undefined,
      content_type: query.content_type || undefined,
      status: 'published',
    })

    const items = response.items || []
    total.value = response.total || 0

    const nextResources = reset ? [] : [...resources.value]
    const existingIds = new Set(nextResources.map((item) => item.id))
    for (const item of items) {
      if (!existingIds.has(item.id)) {
        nextResources.push(item)
      }
    }

    resources.value = nextResources
    query.page = page
    finished.value = items.length < query.size || (total.value > 0 && resources.value.length >= total.value)
  } catch (error) {
    if (reset) {
      resources.value = []
      total.value = 0
    }
    message.error(error instanceof Error ? error.message : '加载精选内容失败')
  } finally {
    if (isFirstPage) {
      loading.value = false
    } else {
      loadingMore.value = false
    }
  }
}

async function resetAndFetch() {
  finished.value = false
  total.value = 0
  resources.value = []
  query.page = 1
  await fetchResources(1, true)
}

async function loadMore() {
  if (loading.value || loadingMore.value || finished.value) {
    return
  }
  await fetchResources(query.page + 1)
}

function handleSearch() {
  void resetAndFetch()
}

function handleTabChange(tab: 'recommended' | 'featured') {
  if (tab === 'recommended') {
    void router.push('/resource/community')
  }
}

function goToDetail(resourceId: number) {
  void router.push({ path: `/resource/detail/${resourceId}`, query: { from: 'featured' } })
}
</script>

<style scoped>
.featured-page {
  background:
    radial-gradient(circle at top center, rgba(46, 46, 46, 0.4), transparent 24%),
    linear-gradient(180deg, #060606 0%, #0b0b0c 36%, #040404 100%);
}

.featured-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - var(--v2-bottomnav-height));
}

.featured-topbar {
  position: sticky;
  top: 0;
  z-index: 12;
  padding-top: 2px;
  background: linear-gradient(180deg, rgba(6, 6, 6, 0.96) 0%, rgba(6, 6, 6, 0.88) 78%, rgba(6, 6, 6, 0) 100%);
  backdrop-filter: blur(16px);
}

.featured-loading,
.featured-empty {
  display: flex;
  flex: 1;
  min-height: 42vh;
  align-items: center;
  justify-content: center;
}

.featured-empty :deep(.ant-empty-description) {
  color: rgba(255, 255, 255, 0.58);
}

.featured-loading :deep(.ant-spin-dot-item),
.featured-footer-state :deep(.ant-spin-dot-item) {
  background-color: rgba(255, 255, 255, 0.9);
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 12px;
}

.featured-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
}

.featured-card:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.38);
  outline-offset: 4px;
  border-radius: 20px;
}

.featured-card :deep(.featured-card-cover.resource-card-cover) {
  height: auto;
  aspect-ratio: 16 / 10;
  border-radius: 18px;
  background: #141414;
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.28);
}

.featured-card :deep(.featured-card-cover .cover-media) {
  background: #141414;
}

.featured-card :deep(.featured-card-cover .cover-fallback) {
  border-radius: 18px;
}

.featured-card :deep(.featured-card-cover .video-indicator) {
  right: 12px;
  bottom: 12px;
  width: 38px;
  height: 38px;
  background: rgba(0, 0, 0, 0.58);
}

.featured-title {
  margin: 0;
  padding: 0 2px;
  color: rgba(255, 255, 255, 0.94);
  font-size: 14px;
  line-height: 1.6;
  font-weight: 600;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.featured-load-trigger {
  width: 100%;
  height: 1px;
}

.featured-footer-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 4px 0 10px;
  color: rgba(255, 255, 255, 0.56);
  font-size: 13px;
}

@media (min-width: 769px) {
  .featured-shell {
    min-height: 100vh;
    gap: 22px;
  }

  .featured-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 22px 18px;
  }

  .featured-title {
    font-size: 15px;
  }
}
</style>

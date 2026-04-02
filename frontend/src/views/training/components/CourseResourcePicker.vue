<template>
  <a-modal
    :open="open"
    title="选择课程资源"
    :footer="null"
    width="720px"
    @update:open="$emit('update:open', $event)"
  >
    <div class="picker-toolbar">
      <a-input-search
        v-model:value="search"
        placeholder="搜索课程名称"
        style="width: 280px"
        allow-clear
        @search="doSearch"
      />
    </div>

    <a-spin :spinning="loading">
      <a-empty v-if="!loading && !list.length" description="暂无课程资源" />
      <div v-else class="picker-list">
        <div v-for="item in list" :key="item.id" class="picker-item">
          <div class="picker-item-info">
            <div class="picker-item-title">{{ item.title }}</div>
            <div class="picker-item-meta">
              <span v-if="item.category">{{ categoryLabel(item.category) }}</span>
              <span v-if="item.instructorName">{{ item.instructorName }}</span>
              <span v-if="item.chapterCount">{{ item.chapterCount }} 章节</span>
            </div>
          </div>
          <a-button type="primary" size="small" @click="handleSelect(item)">选择</a-button>
        </div>
      </div>
    </a-spin>

    <div v-if="total > list.length" class="picker-load-more">
      <a-button type="link" :loading="loading" @click="loadMore">加载更多</a-button>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getCourseResourcesForTraining } from '@/api/training'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'select'])

const search = ref('')
const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)

const categoryLabels = {
  law: '法律法规',
  fraud: '反诈',
  traffic: '交通',
  community: '社区警务',
  cybersec: '网络安全',
  physical: '体能训练',
}

function categoryLabel(cat) {
  return categoryLabels[cat] || cat || ''
}

watch(() => props.open, (val) => {
  if (val) {
    search.value = ''
    page.value = 1
    list.value = []
    fetchList(true)
  }
})

function doSearch() {
  page.value = 1
  fetchList(true)
}

function loadMore() {
  page.value++
  fetchList(false)
}

async function fetchList(reset) {
  loading.value = true
  try {
    const res = await getCourseResourcesForTraining({
      page: page.value,
      size: 20,
      search: search.value.trim() || undefined,
    })
    if (reset) {
      list.value = res.items || []
    } else {
      list.value.push(...(res.items || []))
    }
    total.value = res.total || 0
  } catch {
    if (reset) list.value = []
  } finally {
    loading.value = false
  }
}

function handleSelect(item) {
  emit('select', item)
  emit('update:open', false)
}
</script>

<style scoped>
.picker-toolbar {
  margin-bottom: 16px;
}

.picker-list {
  display: flex;
  flex-direction: column;
  max-height: 420px;
  overflow-y: auto;
}

.picker-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 8px;
  border-bottom: 1px solid #f0f0f0;
  gap: 12px;
}

.picker-item:last-child {
  border-bottom: none;
}

.picker-item-info {
  flex: 1;
  min-width: 0;
}

.picker-item-title {
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-item-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.picker-load-more {
  text-align: center;
  padding: 8px 0;
}
</style>

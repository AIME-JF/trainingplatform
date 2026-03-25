import { computed, ref } from 'vue'

import { getKnowledgePoints } from '@/api/knowledgePoint'

export const KNOWLEDGE_POINT_REMOTE_SIZE = 20
const KNOWLEDGE_POINT_SEARCH_DELAY = 250

function normalizeKnowledgePointItem(item) {
  if (!item) {
    return null
  }
  if (typeof item === 'string') {
    const name = item.trim()
    return name ? { name } : null
  }

  const name = String(item.name || '').trim()
  if (!name) {
    return null
  }

  const id = Number(item.id)
  return {
    ...item,
    id: Number.isFinite(id) && id > 0 ? id : undefined,
    name,
  }
}

export function mergeKnowledgePointOptions(...groups) {
  const merged = []
  const seen = new Set()

  for (const group of groups) {
    for (const rawItem of group || []) {
      const item = normalizeKnowledgePointItem(rawItem)
      if (!item) {
        continue
      }
      const key = item.id ? `id:${item.id}` : `name:${item.name}`
      if (seen.has(key)) {
        continue
      }
      seen.add(key)
      merged.push(item)
    }
  }

  return merged
}

export function createKnowledgePointRemoteSelect(valueMode = 'id') {
  const knowledgePointPinnedOptions = ref([])
  const knowledgePointFetchedOptions = ref([])
  const knowledgePointLoading = ref(false)
  const knowledgePointOptions = computed(() => {
    return mergeKnowledgePointOptions(
      knowledgePointPinnedOptions.value,
      knowledgePointFetchedOptions.value,
    )
  })
  const knowledgePointSelectOptions = computed(() => {
    return knowledgePointOptions.value.map((item) => ({
      value: valueMode === 'name' ? item.name : item.id,
      label: item.name,
    }))
  })

  let latestRequestId = 0
  let searchTimer = null

  function pinKnowledgePointOptions(...groups) {
    knowledgePointPinnedOptions.value = mergeKnowledgePointOptions(
      knowledgePointPinnedOptions.value,
      ...groups,
    )
  }

  async function loadKnowledgePointOptions(search = '') {
    const requestId = ++latestRequestId
    knowledgePointLoading.value = true

    try {
      const keyword = String(search || '').trim()
      const result = await getKnowledgePoints({
        size: KNOWLEDGE_POINT_REMOTE_SIZE,
        isActive: true,
        search: keyword || undefined,
      })
      if (requestId !== latestRequestId) {
        return
      }
      knowledgePointFetchedOptions.value = mergeKnowledgePointOptions(result.items || result || [])
    } finally {
      if (requestId === latestRequestId) {
        knowledgePointLoading.value = false
      }
    }
  }

  function handleKnowledgePointSearch(search = '') {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      loadKnowledgePointOptions(search).catch(() => {})
    }, KNOWLEDGE_POINT_SEARCH_DELAY)
  }

  function handleKnowledgePointFocus() {
    if (knowledgePointOptions.value.length) {
      return
    }
    loadKnowledgePointOptions().catch(() => {})
  }

  return {
    knowledgePointOptions,
    knowledgePointLoading,
    knowledgePointSelectOptions,
    pinKnowledgePointOptions,
    loadKnowledgePointOptions,
    handleKnowledgePointSearch,
    handleKnowledgePointFocus,
  }
}

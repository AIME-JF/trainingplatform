import { computed, ref, type Ref } from 'vue'
import { message } from 'ant-design-vue'

interface TagOption {
  value: string
  label: string
}

interface UseCreatableTagSelectOptions<T> {
  fetchTags: (params?: { search?: string }) => Promise<T[]>
  createTag: (payload: { name: string }) => Promise<T>
  createErrorMessage?: (tagName: string, error: unknown) => string
  searchDelay?: number
}

function extractTagName<T>(item: T | string | null | undefined) {
  if (typeof item === 'string') {
    return item
  }
  if (!item || typeof item !== 'object') {
    return ''
  }
  const value = item as Record<string, unknown>
  return String(value.name || value.value || value.label || '').trim()
}

export function useCreatableTagSelect<T>(
  selectedTagsRef: Ref<string[]>,
  options: UseCreatableTagSelectOptions<T>,
) {
  const tagOptions = ref<TagOption[]>([])
  const tagSearching = ref(false)
  const creatingTagNames = new Set<string>()
  const knownTagNames = new Set<string>()
  let tagSearchTimer: ReturnType<typeof setTimeout> | null = null

  function normalizeTags(tags?: Array<string | null | undefined>) {
    const seen = new Set<string>()
    return (tags || [])
      .map((item) => String(item || '').trim())
      .filter((item) => {
        if (!item || seen.has(item)) {
          return false
        }
        seen.add(item)
        return true
      })
  }

  function rememberTagNames(names: Array<string | null | undefined>) {
    const normalizedTags = normalizeTags(names)
    normalizedTags.forEach((name) => {
      knownTagNames.add(name)
    })
    tagOptions.value = normalizeTags([
      ...tagOptions.value.map((item) => item.value),
      ...normalizedTags,
    ]).map((value) => ({ value, label: value }))
  }

  async function fetchTagOptions(search = '') {
    tagSearching.value = true
    try {
      const items = await options.fetchTags({
        search: search.trim() || undefined,
      })
      const names = (items || []).map(extractTagName).filter(Boolean)
      rememberTagNames(names)
      if (search.trim()) {
        tagOptions.value = normalizeTags([
          ...selectedTagsRef.value,
          ...names,
        ]).map((value) => ({ value, label: value }))
      }
    } finally {
      tagSearching.value = false
    }
  }

  function handleTagSearch(value: string) {
    if (tagSearchTimer) {
      clearTimeout(tagSearchTimer)
    }
    tagSearchTimer = setTimeout(() => {
      void fetchTagOptions(value)
    }, options.searchDelay ?? 250)
  }

  async function handleTagChange(values: string[]) {
    const normalizedTags = normalizeTags(values)
    selectedTagsRef.value = normalizedTags

    const missingTagNames = normalizedTags.filter(
      (name) => !knownTagNames.has(name) && !creatingTagNames.has(name),
    )

    for (const tagName of missingTagNames) {
      creatingTagNames.add(tagName)
      try {
        const createdTag = await options.createTag({ name: tagName })
        const createdName = extractTagName(createdTag) || tagName
        rememberTagNames([createdName])
        selectedTagsRef.value = normalizeTags([...selectedTagsRef.value, createdName])
      } catch (error) {
        selectedTagsRef.value = selectedTagsRef.value.filter((item) => item !== tagName)
        message.error(
          options.createErrorMessage?.(tagName, error)
            || (error instanceof Error ? error.message : '')
            || `标签“${tagName}”创建失败`,
        )
      } finally {
        creatingTagNames.delete(tagName)
      }
    }
  }

  const mergedTagOptions = computed(() => {
    const values = new Set([
      ...tagOptions.value.map((item) => item.value),
      ...normalizeTags(selectedTagsRef.value),
    ])
    return Array.from(values).map((value) => ({ value, label: value }))
  })

  return {
    tagSearching,
    mergedTagOptions,
    normalizeTags,
    fetchTagOptions,
    handleTagSearch,
    handleTagChange,
  }
}

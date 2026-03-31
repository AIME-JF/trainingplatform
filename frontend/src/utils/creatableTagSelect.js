import { computed, ref } from 'vue'
import { message } from 'ant-design-vue'

function extractTagName(item) {
  if (typeof item === 'string') {
    return item
  }
  return item?.name || item?.value || item?.label || ''
}

export function useCreatableTagSelect(selectedTagsRef, options) {
  const tagOptions = ref([])
  const tagSearching = ref(false)
  const creatingTagNames = new Set()
  const knownTagNames = new Set()
  let tagSearchTimer = null

  const mergedTagOptions = computed(() => {
    const values = new Set([
      ...tagOptions.value.map((item) => item.value),
      ...normalizeTags(selectedTagsRef.value),
    ])
    return Array.from(values).map((value) => ({ value, label: value }))
  })

  function normalizeTags(tags) {
    const seen = new Set()
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

  function rememberTagNames(names) {
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
        search: search?.trim() || undefined,
      })
      const names = (items || []).map(extractTagName).filter(Boolean)
      rememberTagNames(names)
      if (search?.trim()) {
        tagOptions.value = normalizeTags([
          ...normalizeTags(selectedTagsRef.value),
          ...names,
        ]).map((value) => ({ value, label: value }))
      }
    } finally {
      tagSearching.value = false
    }
  }

  function handleTagSearch(value) {
    clearTimeout(tagSearchTimer)
    tagSearchTimer = setTimeout(() => {
      fetchTagOptions(value).catch(() => {})
    }, options.searchDelay ?? 250)
  }

  async function handleTagChange(values) {
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
            || error?.message
            || `标签“${tagName}”创建失败`,
        )
      } finally {
        creatingTagNames.delete(tagName)
      }
    }
  }

  return {
    tagSearching,
    mergedTagOptions,
    normalizeTags,
    fetchTagOptions,
    handleTagSearch,
    handleTagChange,
  }
}

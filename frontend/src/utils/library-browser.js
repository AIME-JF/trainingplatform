export const LIBRARY_CATEGORIES = [
  { key: 'all', label: '全部类型', hint: '查看当前范围内全部知识点与资源' },
  { key: 'video', label: '视频', hint: 'MP4 课件视频', category: 'video' },
  { key: 'document', label: '文档', hint: 'PDF / PPT / DOC', category: 'document' },
  { key: 'image', label: '图片', hint: 'JPG / PNG / WEBP / GIF', category: 'image' },
  { key: 'audio', label: '音频', hint: 'MP3 / WAV / M4A', category: 'audio' },
  { key: 'knowledge', label: '知识点', hint: '富文本知识点卡片', category: 'knowledge' },
  { key: 'aiGenerated', label: 'AI教学资源', hint: '教学资源生成后自动入库的课件', sourceKind: 'ai_generated' },
]

export function resolveLibraryCategoryFilter(categoryKey) {
  const matched = LIBRARY_CATEGORIES.find((item) => item.key === categoryKey)
  return {
    category: matched?.category,
    sourceKind: matched?.sourceKind,
  }
}

export function buildLibraryTreeData(nodes) {
  return (nodes || []).map((node) => ({
    key: node.id,
    title: node.name,
    itemCount: node.itemCount || 0,
    children: buildLibraryTreeData(node.children || []),
  }))
}

export function findLibraryFolderName(nodes, folderId) {
  for (const node of nodes || []) {
    if (Number(node.id) === Number(folderId)) {
      return node.name
    }
    const childName = findLibraryFolderName(node.children || [], folderId)
    if (childName) {
      return childName
    }
  }
  return ''
}

export function formatLibraryFileMeta(item) {
  if (item?.contentType === 'knowledge') {
    return '知识点卡片'
  }
  const size = Number(item?.size || 0)
  if (size >= 1024 * 1024) {
    return `${(size / 1024 / 1024).toFixed(1)} MB`
  }
  if (size >= 1024) {
    return `${Math.round(size / 1024)} KB`
  }
  return `${size} B`
}

export function getLibraryTypeLabel(contentType) {
  const map = {
    video: '视频',
    document: '文档',
    image: '图片',
    audio: '音频',
    knowledge: '知识点',
  }
  return map[contentType || ''] || contentType || '资源'
}

export function flattenLibraryFolders(nodes, depth = 0) {
  const result = []
  ;(nodes || []).forEach((node) => {
    result.push({
      value: node.id,
      label: `${'  '.repeat(depth)}${node.name}`,
    })
    result.push(...flattenLibraryFolders(node.children || [], depth + 1))
  })
  return result
}

export function getLibraryTypeIcon(contentType) {
  const map = {
    video: 'VID',
    document: 'DOC',
    image: 'IMG',
    audio: 'AUD',
    knowledge: 'TXT',
  }
  return map[contentType || ''] || 'FILE'
}

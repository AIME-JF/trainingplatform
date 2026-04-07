import type { LibraryFolderResponse, LibraryItemResponse } from '@/api/library'

export interface LibraryTreeNode {
  key: number
  title: string
  itemCount: number
  children: LibraryTreeNode[]
}

export interface LibraryCategoryOption {
  key: string
  label: string
  hint: string
  category?: LibraryItemResponse['content_type']
  sourceKind?: LibraryItemResponse['source_kind']
}

export const LIBRARY_CATEGORIES: ReadonlyArray<LibraryCategoryOption> = [
  { key: 'all', label: '全部类型', hint: '查看当前范围内全部资源' },
  { key: 'video', label: '视频', hint: 'MP4 课件视频', category: 'video' },
  { key: 'document', label: '文档', hint: 'PDF / PPT / DOC', category: 'document' },
  { key: 'image', label: '图片', hint: 'JPG / PNG / WEBP / GIF', category: 'image' },
  { key: 'audio', label: '音频', hint: 'MP3 / WAV / M4A', category: 'audio' },
  { key: 'knowledge', label: '知识点', hint: '富文本知识卡片', category: 'knowledge' },
  { key: 'ai_generated', label: 'AI教学资源', hint: '教学资源生成后自动入库的课件', sourceKind: 'ai_generated' },
]

export function resolveLibraryCategoryFilter(categoryKey: string) {
  const matched = LIBRARY_CATEGORIES.find((item) => item.key === categoryKey)
  return {
    category: matched?.category,
    source_kind: matched?.sourceKind,
  }
}

export function buildLibraryTreeData(nodes: LibraryFolderResponse[]): LibraryTreeNode[] {
  return (nodes || []).map((node) => ({
    key: node.id,
    title: node.name,
    itemCount: node.item_count || 0,
    children: buildLibraryTreeData(node.children || []),
  }))
}

export function flattenLibraryFolders(
  nodes: LibraryFolderResponse[],
  depth = 0,
): Array<{ value: number; label: string }> {
  const result: Array<{ value: number; label: string }> = []
  ;(nodes || []).forEach((node) => {
    result.push({
      value: node.id,
      label: `${'　'.repeat(depth)}${node.name}`,
    })
    result.push(...flattenLibraryFolders(node.children || [], depth + 1))
  })
  return result
}

export function findLibraryFolderName(nodes: LibraryFolderResponse[], folderId: number): string {
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

export function formatLibraryDateTime(value?: string | null) {
  if (!value) {
    return '-'
  }
  return String(value).replace('T', ' ').slice(0, 16)
}

export function formatLibraryFileMeta(item: LibraryItemResponse) {
  if (item.content_type === 'knowledge') {
    return '知识卡片'
  }
  const size = Number(item.size || 0)
  if (size >= 1024 * 1024) {
    return `${(size / 1024 / 1024).toFixed(1)} MB`
  }
  if (size >= 1024) {
    return `${Math.round(size / 1024)} KB`
  }
  return `${size} B`
}

export function getLibraryTypeLabel(contentType?: string | null) {
  const map: Record<string, string> = {
    video: '视频',
    document: '文档',
    image: '图片',
    audio: '音频',
    knowledge: '知识点',
  }
  return map[contentType || ''] || contentType || '资源'
}

export function getLibraryTypeIcon(contentType?: string | null) {
  const map: Record<string, string> = {
    video: 'VID',
    document: 'DOC',
    image: 'IMG',
    audio: 'AUD',
    knowledge: 'TXT',
  }
  return map[contentType || ''] || 'FILE'
}

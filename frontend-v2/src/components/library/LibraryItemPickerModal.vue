<template>
  <a-modal
    :open="open"
    title="从资源库中选择资源"
    :width="1180"
    ok-text="确定关联"
    cancel-text="取消"
    :confirm-loading="confirmLoading"
    :destroy-on-close="true"
    @ok="handleConfirm"
    @cancel="closeModal"
  >
    <div class="picker-shell">
      <aside class="picker-sidebar">
        <section class="picker-side-block">
          <div class="picker-side-title">分类标签</div>
          <div class="picker-category-stack">
            <button
              v-for="category in categories"
              :key="category.key"
              type="button"
              class="picker-category-btn"
              :class="{ active: selectedCategory === category.key }"
              @click="selectCategory(category.key)"
            >
              <span>{{ category.label }}</span>
            </button>
          </div>
        </section>

        <section class="picker-side-block">
          <div class="picker-folder-head">
            <span class="picker-side-title">我的文件夹</span>
            <span>{{ folders.length }} 项</span>
          </div>
          <button
            type="button"
            class="picker-root-entry"
            :class="{ active: selectedFolderId === null }"
            @click="selectedFolderId = null"
          >
            根目录
          </button>
          <a-tree
            v-if="folders.length"
            :tree-data="treeData"
            :selected-keys="selectedFolderKeys"
            block-node
            @select="handleFolderSelect"
          >
            <template #title="{ title, key, itemCount }">
              <div class="picker-folder-node">
                <button type="button" class="picker-folder-link" @click.stop="selectFolderKey(key)">
                  {{ title }}
                </button>
                <span class="picker-folder-count">{{ itemCount || 0 }}</span>
              </div>
            </template>
          </a-tree>
          <a-empty v-else description="暂无文件夹" />
        </section>
      </aside>

      <section class="picker-main">
        <div class="picker-toolbar">
          <a-input-search
            v-model:value="searchKeyword"
            allow-clear
            placeholder="搜索标题"
            class="picker-search"
            @search="handleSearch"
          />
          <div class="picker-toolbar-meta">
            <span>{{ currentFilterDescription }}</span>
            <span>按住 Ctrl + 左键可多选</span>
            <strong>已选 {{ selectedIds.length }} 项</strong>
          </div>
        </div>

        <a-spin :spinning="loading">
          <div v-if="items.length" class="picker-grid">
            <article
              v-for="item in items"
              :key="item.id"
              class="picker-card"
              :class="{
                selected: isSelected(item.id),
                disabled: isBound(item.id),
              }"
              @click="handleCardClick($event, item)"
            >
              <div class="picker-card-cover" :class="`type-${item.content_type}`">
                <span>{{ getLibraryTypeIcon(item.content_type) }}</span>
              </div>
              <div class="picker-card-body">
                <div class="picker-card-top">
                  <div class="picker-card-title-wrap">
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.folder_name || '根目录' }}</p>
                  </div>
                  <a-tag v-if="isBound(item.id)" color="default">已关联</a-tag>
                  <a-tag v-else-if="isSelected(item.id)" color="blue">已选中</a-tag>
                  <a-tag v-else-if="item.source_kind === 'ai_generated'" color="cyan">AI教学资源</a-tag>
                </div>
                <div class="picker-card-meta">
                  <span>{{ getLibraryTypeLabel(item.content_type) }}</span>
                  <span>{{ item.owner_name || '-' }}</span>
                  <span>{{ formatLibraryFileMeta(item) }}</span>
                </div>
              </div>
            </article>
          </div>
          <a-empty v-else description="当前筛选下暂无资源" class="picker-empty" />
        </a-spin>
      </section>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { LibraryFolderResponse, LibraryItemResponse } from '@/api/library'
import { listLibraryFolders, listLibraryItems } from '@/api/library'
import {
  buildLibraryTreeData,
  findLibraryFolderName,
  formatLibraryFileMeta,
  getLibraryTypeIcon,
  getLibraryTypeLabel,
  LIBRARY_CATEGORIES,
  resolveLibraryCategoryFilter,
} from '@/utils/library-browser'

const props = withDefaults(defineProps<{
  open?: boolean
  confirmLoading?: boolean
  boundItemIds?: number[]
}>(), {
  open: false,
  confirmLoading: false,
  boundItemIds: () => [],
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [value: number[]]
}>()

const categories = LIBRARY_CATEGORIES
const loading = ref(false)
const folders = ref<LibraryFolderResponse[]>([])
const items = ref<LibraryItemResponse[]>([])
const selectedCategory = ref<string>('all')
const selectedFolderId = ref<number | null>(null)
const searchKeyword = ref('')
const appliedKeyword = ref('')
const selectedIds = ref<number[]>([])

const treeData = computed(() => buildLibraryTreeData(folders.value))
const selectedFolderKeys = computed(() => (selectedFolderId.value ? [selectedFolderId.value] : []))
const currentFilterDescription = computed(() => {
  const category = categories.find((item) => item.key === selectedCategory.value)?.label || '全部类型'
  const folderName = selectedFolderId.value
    ? findLibraryFolderName(folders.value, selectedFolderId.value)
    : '根目录'
  return `当前查看 ${folderName} 下的 ${category}`
})

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      return
    }
    resetState()
    await Promise.all([fetchFolders(), fetchItems()])
  },
)

watch(
  [selectedCategory, selectedFolderId],
  () => {
    if (props.open) {
      void fetchItems()
    }
  },
)

function resetState() {
  selectedCategory.value = 'all'
  selectedFolderId.value = null
  searchKeyword.value = ''
  appliedKeyword.value = ''
  selectedIds.value = []
  items.value = []
}

async function fetchFolders() {
  try {
    folders.value = await listLibraryFolders()
  } catch (error) {
    folders.value = []
    message.error(error instanceof Error ? error.message : '加载文件夹失败')
  }
}

async function fetchItems() {
  loading.value = true
  try {
    const filters = resolveLibraryCategoryFilter(selectedCategory.value)
    const response = await listLibraryItems({
      page: 1,
      size: -1,
      scope: 'private',
      category: filters.category,
      folder_id: selectedFolderId.value,
      search: appliedKeyword.value || undefined,
      source_kind: filters.source_kind,
    })
    items.value = response.items || []
  } catch (error) {
    items.value = []
    message.error(error instanceof Error ? error.message : '加载资源失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  appliedKeyword.value = searchKeyword.value.trim()
  void fetchItems()
}

function selectCategory(categoryKey: string) {
  selectedCategory.value = categoryKey
}

function handleFolderSelect(keys: Array<string | number>) {
  const [folderId] = keys || []
  selectedFolderId.value = folderId ? Number(folderId) : null
}

function selectFolderKey(folderId: string | number) {
  selectedFolderId.value = Number(folderId)
}

function isBound(itemId: number) {
  return props.boundItemIds.includes(itemId)
}

function isSelected(itemId: number) {
  return selectedIds.value.includes(itemId)
}

function handleCardClick(event: MouseEvent, item: LibraryItemResponse) {
  if (isBound(item.id)) {
    return
  }
  if (event.ctrlKey || event.metaKey) {
    toggleSelected(item.id)
    return
  }
  selectedIds.value = [item.id]
}

function toggleSelected(itemId: number) {
  if (isSelected(itemId)) {
    selectedIds.value = selectedIds.value.filter((id) => id !== itemId)
    return
  }
  selectedIds.value = [...selectedIds.value, itemId]
}

function handleConfirm() {
  if (!selectedIds.value.length) {
    message.warning('请至少选择一个资源')
    return
  }
  emit('confirm', [...selectedIds.value])
}

function closeModal() {
  emit('update:open', false)
}
</script>

<style scoped>
.picker-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  min-height: 560px;
}

.picker-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.picker-side-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--v2-border-light);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(248, 249, 255, 0.92) 0%, #fff 100%);
}

.picker-side-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.picker-category-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.picker-category-btn {
  border: 1px solid var(--v2-border);
  border-radius: 14px;
  background: #fff;
  padding: 12px 14px;
  min-height: 44px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.picker-category-btn span {
  color: var(--v2-text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.picker-category-btn.active {
  border-color: rgba(59, 130, 246, 0.32);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(99, 102, 241, 0.12) 100%);
  box-shadow: 0 10px 22px rgba(59, 130, 246, 0.12);
}

.picker-category-btn.active span {
  color: #2457d6;
}

.picker-folder-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--v2-text-muted);
  font-size: 12px;
}

.picker-root-entry {
  border: none;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.04);
  color: var(--v2-text-secondary);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 12px;
  cursor: pointer;
  text-align: left;
}

.picker-root-entry.active {
  background: rgba(59, 130, 246, 0.1);
  color: #2457d6;
}

.picker-folder-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.picker-folder-link {
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: left;
  padding: 0;
}

.picker-folder-count {
  color: var(--v2-text-muted);
  font-size: 12px;
}

.picker-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.picker-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.picker-search {
  max-width: 360px;
}

.picker-toolbar-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.picker-toolbar-meta strong {
  color: var(--v2-text-primary);
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.picker-card {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--v2-border-light);
  border-radius: 18px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.picker-card:hover {
  border-color: rgba(59, 130, 246, 0.28);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.picker-card.selected {
  border-color: rgba(59, 130, 246, 0.42);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);
  box-shadow: 0 16px 30px rgba(59, 130, 246, 0.14);
}

.picker-card.disabled {
  opacity: 0.68;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.picker-card-cover {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #fff;
}

.picker-card-cover.type-video { background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%); }
.picker-card-cover.type-document { background: linear-gradient(135deg, #0f766e 0%, #0891b2 100%); }
.picker-card-cover.type-image { background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%); }
.picker-card-cover.type-audio { background: linear-gradient(135deg, #dc2626 0%, #ec4899 100%); }
.picker-card-cover.type-knowledge { background: linear-gradient(135deg, #059669 0%, #10b981 100%); }

.picker-card-body {
  flex: 1;
  min-width: 0;
}

.picker-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.picker-card-title-wrap {
  min-width: 0;
}

.picker-card-title-wrap h4 {
  margin: 0;
  font-size: 14px;
  color: var(--v2-text-primary);
  line-height: 1.5;
  word-break: break-word;
}

.picker-card-title-wrap p {
  margin: 6px 0 0;
  color: var(--v2-text-muted);
  font-size: 12px;
}

.picker-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.picker-empty {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1100px) {
  .picker-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .picker-shell {
    grid-template-columns: 1fr;
  }

  .picker-grid {
    grid-template-columns: 1fr;
  }
}
</style>

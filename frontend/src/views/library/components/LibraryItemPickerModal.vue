<template>
  <a-modal
    :open="open"
    title="从知识库中选择资源"
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
              :class="{ selected: isSelected(item.id), disabled: isBound(item.id) }"
              @click="handleCardClick($event, item)"
            >
              <div class="picker-card-cover" :class="`type-${item.contentType}`">
                <span>{{ getLibraryTypeIcon(item.contentType) }}</span>
              </div>
              <div class="picker-card-body">
                <div class="picker-card-top">
                  <div class="picker-card-title-wrap">
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.folderName || '根目录' }}</p>
                  </div>
                  <a-tag v-if="isBound(item.id)" color="default">已关联</a-tag>
                  <a-tag v-else-if="isSelected(item.id)" color="blue">已选中</a-tag>
                  <a-tag v-else-if="item.sourceKind === 'ai_generated'" color="cyan">AI教学资源</a-tag>
                </div>
                <div class="picker-card-meta">
                  <span>{{ getLibraryTypeLabel(item.contentType) }}</span>
                  <span>{{ item.ownerName || '-' }}</span>
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

<script setup>
import { computed, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { getLibraryFolders, getLibraryItems } from '@/api/library'
import {
  LIBRARY_CATEGORIES,
  buildLibraryTreeData,
  findLibraryFolderName,
  formatLibraryFileMeta,
  getLibraryTypeIcon,
  getLibraryTypeLabel,
  resolveLibraryCategoryFilter,
} from '@/utils/library-browser'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  confirmLoading: {
    type: Boolean,
    default: false,
  },
  boundItemIds: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:open', 'confirm'])

const categories = LIBRARY_CATEGORIES
const loading = ref(false)
const folders = ref([])
const items = ref([])
const selectedCategory = ref('all')
const selectedFolderId = ref(null)
const searchKeyword = ref('')
const appliedKeyword = ref('')
const selectedIds = ref([])

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
    folders.value = await getLibraryFolders()
  } catch (error) {
    folders.value = []
    message.error(error?.message || '加载文件夹失败')
  }
}

async function fetchItems() {
  loading.value = true
  try {
    const filters = resolveLibraryCategoryFilter(selectedCategory.value)
    const response = await getLibraryItems({
      page: 1,
      size: -1,
      scope: 'private',
      category: filters.category,
      folderId: selectedFolderId.value,
      search: appliedKeyword.value || undefined,
      sourceKind: filters.sourceKind,
    })
    items.value = response.items || []
  } catch (error) {
    items.value = []
    message.error(error?.message || '加载资源失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  appliedKeyword.value = searchKeyword.value.trim()
  void fetchItems()
}

function selectCategory(categoryKey) {
  selectedCategory.value = categoryKey
}

function handleFolderSelect(keys) {
  const [folderId] = keys || []
  selectedFolderId.value = folderId ? Number(folderId) : null
}

function selectFolderKey(folderId) {
  selectedFolderId.value = Number(folderId)
}

function isBound(itemId) {
  return props.boundItemIds.includes(itemId)
}

function isSelected(itemId) {
  return selectedIds.value.includes(itemId)
}

function handleCardClick(event, item) {
  if (isBound(item.id)) {
    return
  }
  if (event.ctrlKey || event.metaKey) {
    toggleSelected(item.id)
    return
  }
  selectedIds.value = [item.id]
}

function toggleSelected(itemId) {
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
  border: 1px solid #e6edf7;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fbff 0%, #fff 100%);
}

.picker-side-title {
  font-size: 15px;
  font-weight: 700;
  color: #13233b;
}

.picker-category-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.picker-category-btn {
  border: 1px solid #e6edf7;
  border-radius: 14px;
  background: #fff;
  padding: 12px 14px;
  min-height: 44px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.picker-category-btn span {
  color: #5f6f86;
  font-size: 13px;
  font-weight: 600;
}

.picker-category-btn.active {
  border-color: rgba(0, 48, 135, 0.32);
  background: linear-gradient(135deg, rgba(0, 48, 135, 0.08) 0%, rgba(36, 92, 195, 0.08) 100%);
  box-shadow: 0 10px 22px rgba(0, 48, 135, 0.08);
}

.picker-category-btn.active span {
  color: #003087;
}

.picker-folder-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #728096;
  font-size: 12px;
}

.picker-root-entry {
  border: none;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.04);
  color: #1f2d3d;
  font-size: 13px;
  font-weight: 600;
  padding: 10px 12px;
  cursor: pointer;
  text-align: left;
}

.picker-root-entry.active {
  background: #edf4ff;
  color: #003087;
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
  color: #728096;
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
  color: #5f6f86;
  font-size: 13px;
}

.picker-toolbar-meta strong {
  color: #1f2d3d;
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
  border: 1px solid #e7edf6;
  border-radius: 18px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.picker-card:hover {
  border-color: rgba(0, 48, 135, 0.28);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.picker-card.selected {
  border-color: rgba(0, 48, 135, 0.42);
  background: linear-gradient(135deg, rgba(0, 48, 135, 0.05) 0%, rgba(36, 92, 195, 0.08) 100%);
  box-shadow: 0 16px 30px rgba(0, 48, 135, 0.12);
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

.picker-card-cover.type-video { background: linear-gradient(135deg, #123f8f, #245cc3); }
.picker-card-cover.type-document { background: linear-gradient(135deg, #17644d, #2e8b68); }
.picker-card-cover.type-image { background: linear-gradient(135deg, #a45f12, #d1872b); }
.picker-card-cover.type-audio { background: linear-gradient(135deg, #5e1a8c, #8f3cc9); }
.picker-card-cover.type-knowledge { background: linear-gradient(135deg, #394759, #60748c); }

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
  color: #1f2d3d;
  line-height: 1.5;
  word-break: break-word;
}

.picker-card-title-wrap p {
  margin: 6px 0 0;
  color: #728096;
  font-size: 12px;
}

.picker-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  color: #5f6f86;
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

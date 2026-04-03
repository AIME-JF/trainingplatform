<template>
  <div class="library-page" @click="closeContextMenu">
    <QuickUploadModal
      v-model:open="uploadVisible"
      :folder-options="folderOptions"
      :default-folder-id="selectedFolderId"
      @success="handleDataRefresh"
    />
    <KnowledgeCardModal
      v-model:open="knowledgeVisible"
      :folder-options="folderOptions"
      :default-folder-id="selectedFolderId"
      :item-id="editingKnowledgeId"
      :initial-title="editingKnowledgeTitle"
      :initial-content="editingKnowledgeContent"
      @success="handleKnowledgeSaved"
    />
    <MoveItemModal
      v-model:open="moveVisible"
      :item-id="moveTarget?.id || null"
      :current-folder-id="moveTarget?.folder_id || null"
      :folder-options="folderOptions"
      @success="handleDataRefresh"
    />

    <a-modal
      v-model:open="createFolderVisible"
      title="新建文件夹"
      :footer="null"
      :destroy-on-close="true"
      @cancel="resetFolderForm"
    >
      <a-form layout="vertical">
        <a-form-item label="文件夹名称" required>
          <a-input v-model:value="folderForm.name" :maxlength="100" placeholder="请输入文件夹名称" />
        </a-form-item>
        <a-form-item label="父文件夹">
          <a-select v-model:value="folderForm.parent_id" allow-clear placeholder="创建到根目录">
            <a-select-option :value="null">根目录</a-select-option>
            <a-select-option v-for="folder in folderOptions" :key="folder.value" :value="folder.value">
              {{ folder.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <div class="modal-footer">
        <a-button @click="resetFolderForm">取消</a-button>
        <a-button type="primary" :loading="folderSubmitting" @click="handleCreateFolder">创建文件夹</a-button>
      </div>
    </a-modal>

    <a-modal
      v-model:open="previewVisible"
      :title="previewItem?.title || '资源预览'"
      :width="960"
      :footer="null"
      :destroy-on-close="true"
    >
      <div v-if="previewItem" class="preview-panel">
        <div class="preview-meta">
          <a-tag color="blue">{{ getTypeLabel(previewItem.content_type) }}</a-tag>
          <a-tag v-if="previewItem.is_public" color="gold">公共资源</a-tag>
          <span>{{ previewItem.owner_name || '-' }}</span>
          <span>{{ formatDateTime(previewItem.updated_at || previewItem.created_at) }}</span>
        </div>

        <video
          v-if="previewItem.content_type === 'video' && previewItem.file_url"
          :src="previewItem.file_url"
          controls
          class="preview-media"
        />
        <audio
          v-else-if="previewItem.content_type === 'audio' && previewItem.file_url"
          :src="previewItem.file_url"
          controls
          class="preview-audio"
        />
        <div v-else-if="previewItem.content_type === 'image' && previewItem.file_url" class="preview-image-stage">
          <img :src="previewItem.file_url" :alt="previewItem.title" class="preview-image" />
        </div>
        <div v-else-if="previewItem.content_type === 'document' && previewItem.file_url" class="preview-document">
          <iframe :src="previewItem.file_url" class="preview-iframe" title="资源文档预览" />
          <a-button type="link" :href="previewItem.file_url" target="_blank">在新窗口打开文档</a-button>
        </div>
        <div v-else-if="previewItem.content_type === 'knowledge'" class="preview-knowledge" v-html="previewItem.knowledge_content_html" />
        <a-empty v-else description="当前资源暂无可预览内容" />
      </div>
    </a-modal>

    <header class="library-header">
      <div class="header-copy">
        <span class="header-kicker">Library</span>
        <h1>资源库</h1>
        <p>教学文件统一保存在个人资源库，按固定类型和自建文件夹整理，再决定是否共享到公共资源。</p>
      </div>
      <a-radio-group v-model:value="scopeTab" button-style="solid" @change="handleScopeChange">
        <a-radio-button value="private">私人资源</a-radio-button>
        <a-radio-button value="public">公共资源</a-radio-button>
      </a-radio-group>
    </header>

    <div class="library-shell">
      <aside class="library-sidebar">
        <div class="sidebar-card sidebar-head">
          <div>
            <div class="sidebar-title">分类与文件夹</div>
            <div class="sidebar-sub">固定类型在上，自建文件夹在下。</div>
          </div>
          <a-button type="primary" size="small" :disabled="scopeTab !== 'private'" @click="openCreateFolder">添加</a-button>
        </div>

        <div class="sidebar-card category-list">
          <button
            v-for="category in categories"
            :key="category.key"
            type="button"
            class="category-button"
            :class="{ active: selectedCategory === category.key }"
            @click="handleCategorySelect(category.key)"
          >
            <span>{{ category.label }}</span>
            <small>{{ category.hint }}</small>
          </button>
        </div>

        <div class="sidebar-card folder-panel" :class="{ disabled: scopeTab !== 'private' }">
          <div class="folder-panel-head">
            <span>我的文件夹</span>
            <span v-if="scopeTab === 'private'">{{ folders.length }} 项</span>
          </div>
          <a-empty v-if="scopeTab !== 'private'" description="公共资源只按固定类型浏览" />
          <template v-else>
            <button type="button" class="root-entry" :class="{ active: selectedFolderId === null }" @click="selectedFolderId = null">
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
                <div class="folder-node">
                  <button type="button" class="folder-link" @click.stop="selectFolderKey(key)">
                    {{ title }}
                  </button>
                  <span class="folder-count">{{ itemCount || 0 }}</span>
                  <a-button type="text" size="small" danger @click.stop="handleDeleteFolder(Number(key))">删除</a-button>
                </div>
              </template>
            </a-tree>
            <a-empty v-else description="还没有文件夹" />
          </template>
        </div>
      </aside>

      <section class="library-main">
        <div class="main-toolbar">
          <div class="toolbar-copy">
            <h2>{{ scopeTab === 'private' ? '我的资源' : '公共资源' }}</h2>
            <p>{{ currentFilterDescription }}</p>
          </div>
          <div class="toolbar-actions">
            <a-input-search
              v-model:value="searchKeyword"
              allow-clear
              placeholder="搜索标题"
              class="toolbar-search"
              @search="fetchItems"
            />
            <a-button v-if="scopeTab === 'private'" type="primary" @click="uploadVisible = true">批量导入</a-button>
            <a-button v-if="scopeTab === 'private'" @click="openKnowledgeCreate">新建知识点</a-button>
          </div>
        </div>

        <a-spin :spinning="loading">
          <div v-if="items.length" class="item-grid">
            <article
              v-for="item in items"
              :key="item.id"
              class="item-card"
              @click="openPreview(item)"
              @contextmenu.prevent="showContextMenu($event, item)"
            >
              <div class="item-cover" :class="`type-${item.content_type}`">
                <span>{{ getTypeIcon(item.content_type) }}</span>
              </div>
              <div class="item-content">
                <div class="item-top">
                  <div>
                    <h3>{{ item.title }}</h3>
                    <p>{{ item.folder_name || '根目录' }}</p>
                  </div>
                  <a-tag :color="item.is_public ? 'gold' : 'default'">{{ item.is_public ? '公共' : '私人' }}</a-tag>
                </div>
                <div class="item-bottom">
                  <div class="item-bottom-meta">
                    <span>{{ getTypeLabel(item.content_type) }}</span>
                    <span>{{ item.owner_name || '-' }}</span>
                    <span>{{ formatFileMeta(item) }}</span>
                  </div>
                  <a-button
                    v-if="scopeTab === 'private'"
                    type="text"
                    size="small"
                    @click.stop="showActionMenuFromButton($event, item)"
                  >
                    更多
                  </a-button>
                </div>
              </div>
            </article>
          </div>
          <a-empty v-else description="当前筛选下暂无资源" />
        </a-spin>
      </section>
    </div>

    <div
      v-if="contextMenu.visible && contextMenu.item"
      class="context-menu"
      :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
    >
      <button type="button" @click="handleMoveItem(contextMenu.item)">移动到文件夹</button>
      <button type="button" @click="toggleShare(contextMenu.item)">
        {{ contextMenu.item.is_public ? '取消公开' : '共享到公共资源' }}
      </button>
      <button
        v-if="contextMenu.item.content_type === 'knowledge'"
        type="button"
        @click="openKnowledgeEdit(contextMenu.item)"
      >
        编辑知识点
      </button>
      <button type="button" class="danger" @click="handleDeleteItem(contextMenu.item)">删除资源</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Modal, message } from 'ant-design-vue'
import type { LibraryFolderResponse, LibraryItemResponse } from '@/api/library'
import {
  createLibraryFolder,
  deleteLibraryFolder,
  deleteLibraryItem,
  getLibraryItemDetail,
  listLibraryFolders,
  listLibraryItems,
  shareLibraryItem,
  unshareLibraryItem,
} from '@/api/library'
import QuickUploadModal from '@/components/library/QuickUploadModal.vue'
import KnowledgeCardModal from '@/components/library/KnowledgeCardModal.vue'
import MoveItemModal from '@/components/library/MoveItemModal.vue'

interface LibraryTreeNode {
  key: number
  title: string
  itemCount: number
  children: LibraryTreeNode[]
}

const categories = [
  { key: 'all', label: '全部类型', hint: '查看当前范围内全部资源' },
  { key: 'video', label: '视频', hint: 'MP4 课件视频' },
  { key: 'document', label: '文档', hint: 'PDF / PPT / DOC' },
  { key: 'image', label: '图片', hint: 'JPG / PNG / WEBP / GIF' },
  { key: 'audio', label: '音频', hint: 'MP3 / WAV / M4A' },
  { key: 'knowledge', label: '知识点', hint: '富文本知识卡片' },
] as const

const loading = ref(false)
const items = ref<LibraryItemResponse[]>([])
const folders = ref<LibraryFolderResponse[]>([])
const scopeTab = ref<'private' | 'public'>('private')
const selectedCategory = ref<string>('all')
const selectedFolderId = ref<number | null>(null)
const searchKeyword = ref('')
const uploadVisible = ref(false)
const knowledgeVisible = ref(false)
const moveVisible = ref(false)
const previewVisible = ref(false)
const previewItem = ref<LibraryItemResponse | null>(null)
const moveTarget = ref<LibraryItemResponse | null>(null)
const editingKnowledgeId = ref<number | null>(null)
const editingKnowledgeTitle = ref('')
const editingKnowledgeContent = ref('')
const createFolderVisible = ref(false)
const folderSubmitting = ref(false)

const folderForm = reactive({
  name: '',
  parent_id: null as number | null,
})

const contextMenu = reactive<{
  visible: boolean
  x: number
  y: number
  item: LibraryItemResponse | null
}>({
  visible: false,
  x: 0,
  y: 0,
  item: null,
})

const treeData = computed(() => buildTreeData(folders.value))
const selectedFolderKeys = computed(() => selectedFolderId.value ? [selectedFolderId.value] : [])
const folderOptions = computed(() => flattenFolders(folders.value))
const currentFilterDescription = computed(() => {
  const category = categories.find((item) => item.key === selectedCategory.value)?.label || '全部类型'
  if (scopeTab.value !== 'private') {
    return `当前查看所有教官共享的${category}`
  }
  const folderName = selectedFolderId.value
    ? findFolderName(folders.value, selectedFolderId.value)
    : '根目录'
  return `当前查看${folderName}下的${category}`
})

watch([scopeTab, selectedCategory, selectedFolderId], () => {
  void fetchItems()
})

onMounted(() => {
  void fetchFolders()
  void fetchItems()
  document.addEventListener('click', closeContextMenu)
  window.addEventListener('resize', closeContextMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeContextMenu)
  window.removeEventListener('resize', closeContextMenu)
})

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
    const response = await listLibraryItems({
      page: 1,
      size: -1,
      scope: scopeTab.value,
      category: selectedCategory.value === 'all' ? undefined : selectedCategory.value,
      folder_id: scopeTab.value === 'private' ? selectedFolderId.value : undefined,
      search: searchKeyword.value || undefined,
    })
    items.value = response.items || []
  } catch (error) {
    items.value = []
    message.error(error instanceof Error ? error.message : '加载资源失败')
  } finally {
    loading.value = false
  }
}

function handleScopeChange() {
  closeContextMenu()
  if (scopeTab.value !== 'private') {
    selectedFolderId.value = null
  }
}

function handleCategorySelect(category: string) {
  selectedCategory.value = category
}

function handleFolderSelect(keys: Array<string | number>) {
  const [folderId] = keys || []
  selectedFolderId.value = folderId ? Number(folderId) : null
}

function selectFolderKey(folderId: string | number) {
  selectedFolderId.value = Number(folderId)
}

function buildTreeData(nodes: LibraryFolderResponse[]): LibraryTreeNode[] {
  return (nodes || []).map((node) => ({
    key: node.id,
    title: node.name,
    itemCount: node.item_count || 0,
    children: buildTreeData(node.children || []),
  }))
}

function flattenFolders(nodes: LibraryFolderResponse[], depth = 0): Array<{ value: number; label: string }> {
  const result: Array<{ value: number; label: string }> = []
  ;(nodes || []).forEach((node) => {
    result.push({
      value: node.id,
      label: `${'　'.repeat(depth)}${node.name}`,
    })
    result.push(...flattenFolders(node.children || [], depth + 1))
  })
  return result
}

function findFolderName(nodes: LibraryFolderResponse[], folderId: number): string {
  for (const node of nodes || []) {
    if (Number(node.id) === Number(folderId)) {
      return node.name
    }
    const child = findFolderName(node.children || [], folderId)
    if (child) {
      return child
    }
  }
  return ''
}

function openCreateFolder() {
  folderForm.name = ''
  folderForm.parent_id = selectedFolderId.value
  createFolderVisible.value = true
}

function resetFolderForm() {
  createFolderVisible.value = false
  folderForm.name = ''
  folderForm.parent_id = null
}

async function handleCreateFolder() {
  if (!folderForm.name.trim()) {
    message.warning('请输入文件夹名称')
    return
  }
  folderSubmitting.value = true
  try {
    await createLibraryFolder({
      name: folderForm.name.trim(),
      parent_id: folderForm.parent_id,
    })
    message.success('文件夹已创建')
    resetFolderForm()
    await fetchFolders()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '创建文件夹失败')
  } finally {
    folderSubmitting.value = false
  }
}

async function openPreview(item: LibraryItemResponse) {
  try {
    previewItem.value = await getLibraryItemDetail(item.id)
    previewVisible.value = true
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载资源详情失败')
  }
}

function showContextMenu(event: { clientX: number; clientY: number }, item: LibraryItemResponse) {
  if (scopeTab.value !== 'private') {
    return
  }
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.item = item
}

function showActionMenuFromButton(event: MouseEvent, item: LibraryItemResponse) {
  const rect = (event.currentTarget as HTMLElement | null)?.getBoundingClientRect()
  showContextMenu({
    clientX: rect?.left || 0,
    clientY: (rect?.bottom || 0) + 8,
  }, item)
}

function closeContextMenu() {
  contextMenu.visible = false
  contextMenu.item = null
}

function handleMoveItem(item: LibraryItemResponse) {
  moveTarget.value = item
  moveVisible.value = true
  closeContextMenu()
}

async function toggleShare(item: LibraryItemResponse) {
  try {
    if (item.is_public) {
      await unshareLibraryItem(item.id)
      message.success('已取消公开')
    } else {
      await shareLibraryItem(item.id)
      message.success('已共享到公共资源')
    }
    closeContextMenu()
    await fetchItems()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '操作失败')
  }
}

function openKnowledgeCreate() {
  editingKnowledgeId.value = null
  editingKnowledgeTitle.value = ''
  editingKnowledgeContent.value = ''
  knowledgeVisible.value = true
}

async function openKnowledgeEdit(item: LibraryItemResponse) {
  try {
    const detail = await getLibraryItemDetail(item.id)
    editingKnowledgeId.value = detail.id
    editingKnowledgeTitle.value = detail.title
    editingKnowledgeContent.value = detail.knowledge_content_html || ''
    knowledgeVisible.value = true
    closeContextMenu()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载知识点失败')
  }
}

function handleKnowledgeSaved() {
  knowledgeVisible.value = false
  handleDataRefresh()
}

async function handleDeleteFolder(folderId: number) {
  closeContextMenu()
  Modal.confirm({
    title: '删除文件夹',
    content: '仅空文件夹允许删除。确认继续吗？',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await deleteLibraryFolder(folderId)
        if (Number(selectedFolderId.value) === Number(folderId)) {
          selectedFolderId.value = null
        }
        message.success('文件夹已删除')
        await fetchFolders()
        await fetchItems()
      } catch (error) {
        message.error(error instanceof Error ? error.message : '删除文件夹失败')
      }
    },
  })
}

function handleDeleteItem(item: LibraryItemResponse) {
  closeContextMenu()
  Modal.confirm({
    title: '删除资源',
    content: `确认删除“${item.title}”吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await deleteLibraryItem(item.id)
        message.success('资源已删除')
        await fetchItems()
        await fetchFolders()
      } catch (error) {
        message.error(error instanceof Error ? error.message : '删除资源失败')
      }
    },
  })
}

function handleDataRefresh() {
  void fetchItems()
  void fetchFolders()
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return '-'
  }
  return String(value).replace('T', ' ').slice(0, 16)
}

function formatFileMeta(item: LibraryItemResponse) {
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

function getTypeLabel(contentType?: string | null) {
  const map: Record<string, string> = {
    video: '视频',
    document: '文档',
    image: '图片',
    audio: '音频',
    knowledge: '知识点',
  }
  return map[contentType || ''] || contentType || '资源'
}

function getTypeIcon(contentType?: string | null) {
  const map: Record<string, string> = {
    video: 'VID',
    document: 'DOC',
    image: 'IMG',
    audio: 'AUD',
    knowledge: 'TXT',
  }
  return map[contentType || ''] || 'FILE'
}
</script>

<style scoped>
.library-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
}

.library-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 28px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(255, 209, 118, 0.2), transparent 32%),
    linear-gradient(135deg, #10233c 0%, #16355f 48%, #173861 100%);
  color: #fff;
  box-shadow: var(--v2-shadow-lg);
}

.header-kicker {
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.header-copy h1 {
  margin: 10px 0;
  color: #fff;
  font-size: 32px;
}

.header-copy p {
  margin: 0;
  max-width: 640px;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.8;
}

.library-shell {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
}

.library-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-card,
.library-main {
  border-radius: 22px;
  background: var(--v2-bg-card);
  box-shadow: var(--v2-shadow-sm);
}

.sidebar-head,
.category-list,
.folder-panel,
.library-main {
  padding: 18px;
}

.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.sidebar-title {
  color: var(--v2-text-primary);
  font-size: 16px;
  font-weight: 700;
}

.sidebar-sub {
  margin-top: 4px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.category-button {
  width: 100%;
  border: 1px solid var(--v2-border);
  border-radius: 16px;
  background: var(--v2-bg);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-button span {
  display: block;
  color: var(--v2-text-primary);
  font-weight: 700;
}

.category-button small {
  display: block;
  margin-top: 6px;
  color: var(--v2-text-secondary);
  line-height: 1.5;
}

.category-button.active {
  border-color: rgba(75, 110, 245, 0.35);
  background: var(--v2-primary-light);
}

.folder-panel.disabled {
  opacity: 0.72;
}

.folder-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.root-entry {
  width: 100%;
  margin-bottom: 10px;
  border: 1px solid var(--v2-border);
  border-radius: 14px;
  background: var(--v2-bg);
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
}

.root-entry.active {
  border-color: rgba(75, 110, 245, 0.35);
  background: var(--v2-primary-light);
}

.folder-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.folder-link {
  flex: 1;
  border: 0;
  background: transparent;
  padding: 0;
  text-align: left;
  color: var(--v2-text-primary);
  cursor: pointer;
}

.folder-count {
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.main-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.toolbar-copy h2 {
  margin: 0;
  color: var(--v2-text-primary);
  font-size: 24px;
}

.toolbar-copy p {
  margin: 8px 0 0;
  color: var(--v2-text-secondary);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.toolbar-search {
  width: 240px;
}

.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.item-card {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.item-card:hover {
  transform: translateY(-2px);
  border-color: rgba(75, 110, 245, 0.26);
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.08);
}

.item-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.item-cover.type-video { background: linear-gradient(135deg, #17396f, #2f67ca); }
.item-cover.type-document { background: linear-gradient(135deg, #1a5f49, #2c936d); }
.item-cover.type-image { background: linear-gradient(135deg, #a95d12, #d68b31); }
.item-cover.type-audio { background: linear-gradient(135deg, #672493, #9158d5); }
.item-cover.type-knowledge { background: linear-gradient(135deg, #3a4658, #62768d); }

.item-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
}

.item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.item-top h3 {
  margin: 0;
  color: var(--v2-text-primary);
  font-size: 16px;
}

.item-top p {
  margin: 8px 0 0;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.item-bottom {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.item-bottom-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.preview-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.preview-media,
.preview-iframe {
  width: 100%;
  min-height: 420px;
  border: 0;
  border-radius: 18px;
  background: #09111d;
}

.preview-audio {
  width: 100%;
}

.preview-image-stage {
  display: flex;
  justify-content: center;
  padding: 20px;
  border-radius: 18px;
  background: var(--v2-bg);
}

.preview-image {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
}

.preview-document {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-knowledge {
  padding: 18px;
  border-radius: 18px;
  background: var(--v2-bg);
  line-height: 1.9;
  color: var(--v2-text-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.context-menu {
  position: fixed;
  z-index: 1000;
  min-width: 188px;
  padding: 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(226, 232, 240, 0.96);
  box-shadow: var(--v2-shadow-lg);
}

.context-menu button {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 10px 12px;
  text-align: left;
  border-radius: 10px;
  color: var(--v2-text-primary);
  cursor: pointer;
}

.context-menu button:hover {
  background: var(--v2-bg);
}

.context-menu button.danger {
  color: var(--v2-danger);
}

@media (max-width: 960px) {
  .library-shell {
    grid-template-columns: 1fr;
  }

  .library-header,
  .main-toolbar {
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .toolbar-search {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .library-page {
    padding: 16px 16px 88px;
  }

  .library-header,
  .sidebar-head,
  .category-list,
  .folder-panel,
  .library-main {
    padding: 16px;
  }

  .item-grid {
    grid-template-columns: 1fr;
  }

  .item-card {
    grid-template-columns: 74px minmax(0, 1fr);
  }

  .preview-media,
  .preview-iframe {
    min-height: 260px;
  }
}
</style>

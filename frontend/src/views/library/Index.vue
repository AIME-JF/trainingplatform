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
      :current-folder-id="moveTarget?.folderId || null"
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
          <a-select v-model:value="folderForm.parentId" allow-clear placeholder="创建到根目录">
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
          <a-tag color="blue">{{ getTypeLabel(previewItem.contentType) }}</a-tag>
          <a-tag v-if="previewItem.sourceKind === 'ai_generated'" color="cyan">AI教学资源</a-tag>
          <a-tag v-if="previewItem.isPublic" color="gold">公共资源</a-tag>
          <span>{{ previewItem.ownerName || '-' }}</span>
          <span>{{ formatDateTime(previewItem.updatedAt || previewItem.createdAt) }}</span>
        </div>

        <video
          v-if="previewItem.contentType === 'video' && previewItem.fileUrl"
          :src="previewItem.fileUrl"
          controls
          class="preview-media"
        />
        <audio
          v-else-if="previewItem.contentType === 'audio' && previewItem.fileUrl"
          :src="previewItem.fileUrl"
          controls
          class="preview-audio"
        />
        <div v-else-if="previewItem.contentType === 'image' && previewItem.fileUrl" class="preview-image-stage">
          <img :src="previewItem.fileUrl" :alt="previewItem.title" class="preview-image" />
        </div>
        <div v-else-if="previewItem.contentType === 'document' && previewItem.fileUrl" class="preview-document">
          <iframe :src="previewItem.fileUrl" class="preview-iframe" title="资源文档预览" />
          <a-button type="link" :href="previewItem.fileUrl" target="_blank">在新窗口打开文档</a-button>
        </div>
        <div v-else-if="previewItem.contentType === 'knowledge'" class="preview-knowledge" v-html="previewItem.knowledgeContentHtml" />
        <a-empty v-else description="当前资源暂无可预览内容" />
      </div>
    </a-modal>

    <header class="library-header">
      <div>
        <div class="header-kicker">Instructor Workspace</div>
        <h1>资源库</h1>
        <p>正式教学文件统一归档到个人资源库，按分类和文件夹整理，再决定是否共享到公共资源。</p>
      </div>
    </header>

    <section class="library-controls">
      <div class="controls-intro">
      </div>

      <div class="controls-actions">
        <div class="scope-toggle" :class="{ 'is-public': scopeTab === 'public' }">
          <button
            type="button"
            class="scope-option"
            :class="{ active: scopeTab === 'private' }"
            @click="setScopeTab('private')"
          >
            私人资源
          </button>
          <button
            type="button"
            class="scope-option"
            :class="{ active: scopeTab === 'public' }"
            @click="setScopeTab('public')"
          >
            公共资源
          </button>
        </div>
        <a-input-search
          v-model:value="searchKeyword"
          allow-clear
          size="large"
          placeholder="搜索标题"
          class="toolbar-search"
          @search="fetchItems"
        />
        <a-button
          type="primary"
          size="large"
          :disabled="scopeTab !== 'private'"
          @click="openCreateFolder"
        >
          新建文件夹
        </a-button>
      </div>
    </section>

    <div class="library-shell">
      <aside class="library-sidebar">
        <div class="sidebar-categories">
          <div class="category-heading">
            <div class="sidebar-title">分类标签</div>
          </div>
          <div class="category-stack">
            <button
              v-for="category in categories"
              :key="category.key"
              type="button"
              class="category-button"
              :class="{ active: selectedCategory === category.key }"
              @click="handleCategorySelect(category.key)"
            >
              <span>{{ category.label }}</span>
            </button>
          </div>
        </div>

        <div class="sidebar-block folder-panel" :class="{ disabled: scopeTab !== 'private' }">
          <div class="folder-panel-head">
            <span>我的文件夹</span>
            <span v-if="scopeTab === 'private'">{{ folders.length }} 项</span>
          </div>
          <a-empty v-if="scopeTab !== 'private'" description="公共资源只按固定类型浏览" />
          <template v-else>
            <button
              type="button"
              class="root-entry"
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
                <div class="folder-node">
                  <button type="button" class="folder-link" @click.stop="selectFolderKey(key)">
                    {{ title }}
                  </button>
                  <span class="folder-count">{{ itemCount || 0 }}</span>
                  <a-button type="text" size="small" danger @click.stop="handleDeleteFolder(key)">删除</a-button>
                </div>
              </template>
            </a-tree>
            <a-empty v-else description="还没有文件夹" />
          </template>
        </div>
      </aside>

      <section class="library-main">
        <div class="content-meta">
          <div class="content-meta-head">
            <div>
              <h2>{{ scopeTab === 'private' ? '我的资源' : '公共资源' }}</h2>
              <p>{{ currentFilterDescription }}</p>
            </div>
            <div v-if="scopeTab === 'private'" class="content-actions">
              <a-button type="primary" size="large" @click="uploadVisible = true">批量导入</a-button>
              <a-button size="large" @click="openKnowledgeCreate">新建知识点</a-button>
            </div>
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
              <div class="item-cover" :class="`type-${item.contentType}`">
                <span>{{ getTypeIcon(item.contentType) }}</span>
              </div>
              <div class="item-content">
                <div class="item-top">
                  <div>
                    <h3>{{ item.title }}</h3>
                    <p>{{ item.folderName || '根目录' }}</p>
                  </div>
                  <div class="item-tag-stack">
                    <a-tag v-if="item.sourceKind === 'ai_generated'" color="cyan">AI教学资源</a-tag>
                    <a-tag :color="item.isPublic ? 'gold' : 'default'">{{ item.isPublic ? '公共' : '私人' }}</a-tag>
                  </div>
                </div>
                <div class="item-bottom">
                  <div class="item-bottom-meta">
                    <span>{{ getTypeLabel(item.contentType) }}</span>
                    <span>{{ item.ownerName || '-' }}</span>
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
      <button
        type="button"
        @click="toggleShare(contextMenu.item)"
      >
        {{ contextMenu.item.isPublic ? '取消公开' : '共享到公共资源' }}
      </button>
      <button
        v-if="contextMenu.item.contentType === 'knowledge'"
        type="button"
        @click="openKnowledgeEdit(contextMenu.item)"
      >
        编辑知识点
      </button>
      <button type="button" class="danger" @click="handleDeleteItem(contextMenu.item)">删除资源</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Modal, message } from 'ant-design-vue'
import {
  createLibraryFolder,
  deleteLibraryFolder,
  deleteLibraryItem,
  getLibraryFolders,
  getLibraryItem,
  getLibraryItems,
  shareLibraryItem,
  unshareLibraryItem,
} from '@/api/library'
import QuickUploadModal from './components/QuickUploadModal.vue'
import KnowledgeCardModal from './components/KnowledgeCardModal.vue'
import MoveItemModal from './components/MoveItemModal.vue'

const categories = [
  { key: 'all', label: '全部类型', hint: '查看当前范围内全部资源' },
  { key: 'video', label: '视频', hint: 'MP4 课件视频', category: 'video' },
  { key: 'document', label: '文档', hint: 'PDF / PPT / DOC', category: 'document' },
  { key: 'image', label: '图片', hint: 'JPG / PNG / WEBP / GIF', category: 'image' },
  { key: 'audio', label: '音频', hint: 'MP3 / WAV / M4A', category: 'audio' },
  { key: 'knowledge', label: '知识点', hint: '富文本知识卡片', category: 'knowledge' },
  { key: 'aiGenerated', label: 'AI教学资源', hint: '教学资源生成后自动入库的课件', sourceKind: 'ai_generated' },
]

const loading = ref(false)
const folderLoading = ref(false)
const items = ref([])
const folders = ref([])
const scopeTab = ref('private')
const selectedCategory = ref('all')
const selectedFolderId = ref(null)
const searchKeyword = ref('')
const uploadVisible = ref(false)
const knowledgeVisible = ref(false)
const moveVisible = ref(false)
const previewVisible = ref(false)
const previewItem = ref(null)
const moveTarget = ref(null)
const editingKnowledgeId = ref(null)
const editingKnowledgeTitle = ref('')
const editingKnowledgeContent = ref('')
const createFolderVisible = ref(false)
const folderSubmitting = ref(false)

const folderForm = reactive({
  name: '',
  parentId: null,
})

const contextMenu = reactive({
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

watch(
  [scopeTab, selectedCategory, selectedFolderId],
  () => {
    fetchItems()
  },
)

onMounted(() => {
  fetchFolders()
  fetchItems()
  document.addEventListener('click', closeContextMenu)
  window.addEventListener('resize', closeContextMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeContextMenu)
  window.removeEventListener('resize', closeContextMenu)
})

async function fetchFolders() {
  folderLoading.value = true
  try {
    folders.value = await getLibraryFolders()
  } catch (error) {
    folders.value = []
    message.error(error?.message || '加载文件夹失败')
  } finally {
    folderLoading.value = false
  }
}

async function fetchItems() {
  loading.value = true
  try {
    const filters = resolveCategoryFilter(selectedCategory.value)
    const response = await getLibraryItems({
      page: 1,
      size: -1,
      scope: scopeTab.value,
      category: filters.category,
      folderId: scopeTab.value === 'private' ? selectedFolderId.value : undefined,
      search: searchKeyword.value || undefined,
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

function handleScopeChange() {
  closeContextMenu()
  if (scopeTab.value !== 'private') {
    selectedFolderId.value = null
  }
  fetchItems()
}

function setScopeTab(nextScope) {
  if (scopeTab.value === nextScope) {
    return
  }
  scopeTab.value = nextScope
  handleScopeChange()
}

function handleCategorySelect(category) {
  selectedCategory.value = category
}

function resolveCategoryFilter(categoryKey) {
  const currentCategory = categories.find((item) => item.key === categoryKey)
  return {
    category: currentCategory?.category,
    sourceKind: currentCategory?.sourceKind,
  }
}

function handleFolderSelect(keys) {
  const [folderId] = keys || []
  selectedFolderId.value = folderId ?? null
}

function selectFolderKey(folderId) {
  selectedFolderId.value = Number(folderId)
}

function openCreateFolder() {
  folderForm.name = ''
  folderForm.parentId = selectedFolderId.value
  createFolderVisible.value = true
}

function resetFolderForm() {
  createFolderVisible.value = false
  folderForm.name = ''
  folderForm.parentId = null
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
      parentId: folderForm.parentId,
    })
    message.success('文件夹已创建')
    resetFolderForm()
    await fetchFolders()
  } catch (error) {
    message.error(error?.message || '创建文件夹失败')
  } finally {
    folderSubmitting.value = false
  }
}

function buildTreeData(nodes) {
  return (nodes || []).map((node) => ({
    key: node.id,
    title: node.name,
    itemCount: node.itemCount || 0,
    children: buildTreeData(node.children || []),
  }))
}

function flattenFolders(nodes, depth = 0) {
  const result = []
  ;(nodes || []).forEach((node) => {
    result.push({
      value: node.id,
      label: `${'　'.repeat(depth)}${node.name}`,
    })
    result.push(...flattenFolders(node.children || [], depth + 1))
  })
  return result
}

function findFolderName(nodes, folderId) {
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

async function openPreview(item) {
  try {
    previewItem.value = await getLibraryItem(item.id)
    previewVisible.value = true
  } catch (error) {
    message.error(error?.message || '加载资源详情失败')
  }
}

function showContextMenu(event, item) {
  if (scopeTab.value !== 'private') {
    return
  }
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.item = item
}

function showActionMenuFromButton(event, item) {
  const rect = event.currentTarget?.getBoundingClientRect?.()
  showContextMenu({
    clientX: rect?.left || 0,
    clientY: (rect?.bottom || 0) + 8,
  }, item)
}

function closeContextMenu() {
  contextMenu.visible = false
  contextMenu.item = null
}

function handleMoveItem(item) {
  moveTarget.value = item
  moveVisible.value = true
  closeContextMenu()
}

async function toggleShare(item) {
  try {
    if (item.isPublic) {
      await unshareLibraryItem(item.id)
      message.success('已取消公开')
    } else {
      await shareLibraryItem(item.id)
      message.success('已共享到公共资源')
    }
    closeContextMenu()
    await fetchItems()
  } catch (error) {
    message.error(error?.message || '操作失败')
  }
}

function openKnowledgeCreate() {
  editingKnowledgeId.value = null
  editingKnowledgeTitle.value = ''
  editingKnowledgeContent.value = ''
  knowledgeVisible.value = true
}

async function openKnowledgeEdit(item) {
  try {
    const detail = await getLibraryItem(item.id)
    editingKnowledgeId.value = detail.id
    editingKnowledgeTitle.value = detail.title
    editingKnowledgeContent.value = detail.knowledgeContentHtml || ''
    knowledgeVisible.value = true
    closeContextMenu()
  } catch (error) {
    message.error(error?.message || '加载知识点失败')
  }
}

function handleKnowledgeSaved() {
  knowledgeVisible.value = false
  handleDataRefresh()
}

async function handleDeleteFolder(folderId) {
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
        message.error(error?.message || '删除文件夹失败')
      }
    },
  })
}

function handleDeleteItem(item) {
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
        message.error(error?.message || '删除资源失败')
      }
    },
  })
}

function handleDataRefresh() {
  fetchItems()
  fetchFolders()
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  return String(value).replace('T', ' ').slice(0, 16)
}

function formatFileMeta(item) {
  if (item.contentType === 'knowledge') {
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

function getTypeLabel(contentType) {
  const map = {
    video: '视频',
    document: '文档',
    image: '图片',
    audio: '音频',
    knowledge: '知识点',
  }
  return map[contentType] || contentType || '资源'
}

function getTypeIcon(contentType) {
  const map = {
    video: 'VID',
    document: 'DOC',
    image: 'IMG',
    audio: 'AUD',
    knowledge: 'TXT',
  }
  return map[contentType] || 'FILE'
}
</script>

<style scoped>
.library-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.library-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(234, 192, 72, 0.14), transparent 34%),
    linear-gradient(135deg, #0d2240 0%, #16355f 55%, #102640 100%);
  color: #fff;
}

.header-kicker {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.72);
}

.library-header h1 {
  margin: 10px 0 10px;
  font-size: 32px;
  color: #fff;
}

.library-header p {
  max-width: 640px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.78);
}

.library-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px 24px;
}

.controls-intro {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 180px;
}

.controls-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 1 1 520px;
  flex-wrap: wrap;
  gap: 14px 16px;
}

.library-shell {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
}

.library-sidebar,
.library-main {
  min-width: 0;
}

.library-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: #13233b;
}

.sidebar-sub {
  color: #728096;
  font-size: 12px;
}

.sidebar-categories {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-button {
  border: 1px solid #e6edf7;
  border-radius: 16px;
  background: #f9fbff;
  padding: 14px 16px;
  min-height: 50px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-button span {
  display: block;
  font-weight: 700;
  color: #1f2d3d;
  font-size: 14px;
}

.category-button.active {
  border-color: #003087;
  background: #eef4ff;
  box-shadow: inset 0 0 0 1px rgba(0, 48, 135, 0.08);
}

.sidebar-block {
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.05);
  padding: 18px;
}

.folder-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.folder-panel.disabled {
  opacity: 0.72;
}

.folder-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 13px;
  color: #5f6f86;
}

.root-entry {
  padding: 10px 12px;
  border: 1px solid #e6edf7;
  border-radius: 12px;
  background: #f8fbff;
  text-align: left;
  cursor: pointer;
  width: 100%;
}

.root-entry.active {
  border-color: #003087;
  background: #edf4ff;
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
  text-align: left;
  padding: 0;
  color: #1f2d3d;
  cursor: pointer;
}

.folder-count {
  color: #7a8699;
  font-size: 12px;
}

.library-main {
  min-height: 200px;
}

.content-meta {
  margin-bottom: 18px;
}

.content-meta-head {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 16px 24px;
  flex-wrap: wrap;
}

.content-meta h2 {
  margin: 0;
  font-size: 24px;
  color: #14253e;
}

.content-meta p {
  margin: 8px 0 0;
  color: #728096;
}

.content-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 14px;
}

.scope-toggle {
  position: relative;
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: center;
  min-width: 236px;
  padding: 4px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(0, 48, 135, 0.1), rgba(15, 23, 42, 0.06));
}

.scope-toggle::before {
  content: '';
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc((100% - 8px) / 2);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.12);
  transition: transform 0.24s ease;
}

.scope-toggle.is-public::before {
  transform: translateX(100%);
}

.scope-option {
  position: relative;
  z-index: 1;
  min-width: 0;
  height: 46px;
  border: 0;
  background: transparent;
  padding: 0 18px;
  border-radius: 14px;
  color: #5f6f86;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.2s ease;
}

.scope-option.active {
  color: #003087;
}

.toolbar-search :deep(.ant-input-affix-wrapper),
.toolbar-search :deep(.ant-input-search-button),
.content-actions :deep(.ant-btn),
.controls-actions :deep(.ant-btn) {
  border-radius: 14px;
}

.toolbar-search {
  width: 280px;
}

.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.item-card {
  display: grid;
  grid-template-columns: 90px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  border: 1px solid #e7edf6;
  border-radius: 18px;
  background: #fff;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.item-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 48, 135, 0.18);
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.08);
}

.item-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.item-cover.type-video { background: linear-gradient(135deg, #123f8f, #245cc3); }
.item-cover.type-document { background: linear-gradient(135deg, #17644d, #2e8b68); }
.item-cover.type-image { background: linear-gradient(135deg, #a45f12, #d1872b); }
.item-cover.type-audio { background: linear-gradient(135deg, #5e1a8c, #8f3cc9); }
.item-cover.type-knowledge { background: linear-gradient(135deg, #394759, #60748c); }

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

.item-tag-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.item-top h3 {
  margin: 0;
  color: #17263d;
  font-size: 16px;
}

.item-top p {
  margin: 8px 0 0;
  color: #728096;
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
  color: #5f6f86;
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
  color: #728096;
  font-size: 13px;
}

.preview-media,
.preview-iframe {
  width: 100%;
  min-height: 420px;
  border: 0;
  border-radius: 16px;
  background: #0b1020;
}

.preview-audio {
  width: 100%;
}

.preview-image-stage {
  display: flex;
  justify-content: center;
  padding: 20px;
  border-radius: 16px;
  background: #f7f9fc;
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
  border-radius: 16px;
  background: #f8fafc;
  line-height: 1.9;
  color: #1f2d3d;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.context-menu {
  position: fixed;
  z-index: 1000;
  min-width: 180px;
  padding: 8px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid #e7edf6;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
}

.context-menu button {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 10px 12px;
  text-align: left;
  border-radius: 10px;
  cursor: pointer;
  color: #1f2d3d;
}

.context-menu button:hover {
  background: #f4f8ff;
}

.context-menu button.danger {
  color: #c62828;
}

@media (max-width: 960px) {
  .library-controls {
    flex-direction: column;
    align-items: flex-start;
  }

  .library-shell {
    grid-template-columns: 1fr;
  }

  .controls-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .content-meta-head {
    align-items: stretch;
  }

  .toolbar-search {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .library-header,
  .sidebar-block {
    padding: 16px;
  }

  .library-controls {
    gap: 12px;
  }

  .controls-intro,
  .controls-actions {
    width: 100%;
  }

  .content-actions {
    width: 100%;
  }

  .item-grid {
    grid-template-columns: 1fr;
  }

  .item-card {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .preview-media,
  .preview-iframe {
    min-height: 260px;
  }
}
</style>

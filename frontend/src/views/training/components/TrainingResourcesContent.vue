<template>
  <div class="resources-content">

    <!-- ===== 知识库资源 ===== -->
    <div class="res-section-block">
      <div class="res-section-header">
        <span class="res-section-title">知识库资源</span>
        <a-button
          v-if="canManage"
          type="primary"
          size="small"
          @click="libraryModalVisible = true"
        >
          <PlusOutlined /> 添加知识库资源
        </a-button>
      </div>

      <a-spin :spinning="trainingResLoading">
        <template v-if="trainingResources.length">
          <div class="res-bound-list">
            <div
              v-for="res in trainingResources"
              :key="res.ref_id"
              class="res-bound-item"
            >
              <span class="res-type-icon">{{ contentTypeIcon(res.content_type) }}</span>
              <div class="res-bound-info">
                <div class="res-bound-title">
                  {{ res.title }}
                  <a-tag v-if="res.binding_type === 'library_item'" color="blue" size="small" style="margin-left: 6px">知识库</a-tag>
                  <a-tag v-else color="default" size="small" style="margin-left: 6px">资源库</a-tag>
                </div>
                <div class="res-bound-meta">
                  <span>{{ contentTypeLabel(res.content_type) }}</span>
                  <span v-if="res.uploader_name">{{ res.uploader_name }}</span>
                  <span v-if="res.owner_department_name">{{ res.owner_department_name }}</span>
                </div>
              </div>
              <div class="res-bound-actions">
                <a
                  v-if="res.file_url"
                  :href="res.file_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  style="font-size: 13px; color: #1677ff"
                >查看</a>
                <a-button
                  v-if="canManage"
                  type="link"
                  danger
                  size="small"
                  :loading="removingRefId === res.ref_id"
                  @click="removeTrainingRes(res)"
                >移除</a-button>
              </div>
            </div>
          </div>
        </template>
        <a-empty v-else description="暂无已添加的知识库资源" style="padding: 24px 0" />
      </a-spin>
    </div>

    <a-divider style="margin: 12px 0" />

    <!-- ===== 课程资源 ===== -->
    <div class="res-section-block">
      <div class="res-section-header">
        <span class="res-section-title">课程资源</span>
      </div>
      <a-empty v-if="linkedCourses.length === 0" description="本班暂无关联课程资源的课程" style="margin-top: 16px" />

      <template v-else>
        <a-collapse v-model:activeKey="expandedKeys" :bordered="false" ghost>
          <a-collapse-panel
            v-for="item in linkedCourses"
            :key="String(item.trainingCourse.id)"
            :style="panelStyle"
          >
            <template #header>
              <span class="panel-title">{{ item.trainingCourse.name }}</span>
              <a-tag color="green" style="margin-left: 8px">已关联课程资源</a-tag>
              <span v-if="item.loading" style="margin-left: 8px; font-size: 12px; color: #999">加载中…</span>
              <span v-else-if="item.chapters.length > 0" style="margin-left: 8px; font-size: 12px; color: #999">
                {{ item.chapters.length }} 个章节，{{ boundChapterCount(item) }} 个绑定资源
              </span>
            </template>

            <a-spin :spinning="item.loading">
              <a-empty v-if="!item.loading && item.chapters.length === 0" description="该课程暂无章节" style="padding: 16px 0" />
              <a-table
                v-else
                :data-source="item.chapters"
                :pagination="false"
                row-key="id"
                size="small"
                :show-header="true"
              >
                <a-table-column title="#" key="sortOrder" width="48">
                  <template #default="{ record }">
                    <span style="color: #999">{{ record.sortOrder + 1 }}</span>
                  </template>
                </a-table-column>
                <a-table-column title="章节名称" data-index="title" key="title" />
                <a-table-column title="资源名称" key="resourceTitle" width="240">
                  <template #default="{ record }">
                    <template v-if="record.resourceId">
                      <span class="resource-icon">{{ contentTypeIcon(record.contentType) }}</span>
                      <span>{{ record.resourceTitle || record.resourceFileName || '未命名资源' }}</span>
                    </template>
                    <span v-else style="color: #ccc">—</span>
                  </template>
                </a-table-column>
                <a-table-column title="类型" key="contentType" width="90">
                  <template #default="{ record }">
                    <a-tag v-if="record.resourceId" :color="contentTypeColor(record.contentType)" size="small">
                      {{ record.resourceFileLabel || contentTypeLabel(record.contentType) }}
                    </a-tag>
                    <span v-else style="color: #ccc">—</span>
                  </template>
                </a-table-column>
                <a-table-column title="操作" key="action" width="80">
                  <template #default="{ record }">
                    <a
                      v-if="record.fileUrl"
                      :href="record.fileUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                    >查看</a>
                    <span v-else style="color: #ccc">—</span>
                  </template>
                </a-table-column>
              </a-table>
            </a-spin>
          </a-collapse-panel>
        </a-collapse>

        <div v-if="customCourses.length > 0" style="margin-top: 16px">
          <a-divider style="font-size: 12px; color: #aaa">以下为自定义课程（未关联课程资源）</a-divider>
          <a-list :data-source="customCourses" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.name">
                  <template #description>自定义课程，无章节资源</template>
                </a-list-item-meta>
                <a-tag color="default">自定义</a-tag>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </template>
    </div>

    <!-- 知识库资源选择弹窗 -->
    <a-modal
      v-model:open="libraryModalVisible"
      title="从知识库选择资源"
      ok-text="确认添加"
      cancel-text="取消"
      :width="1100"
      :confirm-loading="libraryConfirmLoading"
      :destroy-on-close="true"
      @ok="confirmLibraryAdd"
    >
      <div class="picker-shell">
        <!-- 侧边栏：分类 + 文件夹 -->
        <aside class="picker-sidebar">
          <div class="picker-side-block">
            <div class="picker-side-title">资源类型</div>
            <div class="picker-category-stack">
              <button
                v-for="cat in libraryCategories"
                :key="cat.key"
                type="button"
                class="picker-category-btn"
                :class="{ active: selectedCategory === cat.key }"
                @click="selectedCategory = cat.key; fetchLibraryItems()"
              >{{ cat.label }}</button>
            </div>
          </div>

          <div class="picker-side-block" style="margin-top: 12px">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
              <span class="picker-side-title">我的文件夹</span>
            </div>
            <div
              class="picker-folder-btn"
              :class="{ active: selectedFolderId === null }"
              @click="selectedFolderId = null; fetchLibraryItems()"
            >全部文件夹</div>
            <div
              v-for="folder in libraryFolders"
              :key="folder.id"
              class="picker-folder-btn"
              :class="{ active: selectedFolderId === folder.id }"
              @click="selectedFolderId = folder.id; fetchLibraryItems()"
            >{{ folder.name }}</div>
          </div>
        </aside>

        <!-- 主区域 -->
        <div class="picker-main">
          <div class="picker-toolbar">
            <a-input-search
              v-model:value="librarySearch"
              allow-clear
              placeholder="搜索标题"
              style="max-width: 320px"
              @search="fetchLibraryItems"
            />
            <span class="picker-meta">
              已选 <strong>{{ selectedLibraryIds.length }}</strong> 项 &nbsp;·&nbsp; 按住 Ctrl 可多选
            </span>
          </div>

          <a-spin :spinning="libraryLoading">
            <div v-if="libraryItems.length" class="picker-grid">
              <div
                v-for="item in libraryItems"
                :key="item.id"
                class="picker-card"
                :class="{
                  'picker-card--selected': isLibrarySelected(item.id),
                  'picker-card--bound': isLibraryBound(item.id),
                }"
                @click="handleLibraryCardClick($event, item)"
              >
                <div class="picker-card-cover" :class="`cover-${item.content_type}`">
                  <span>{{ contentTypeIcon(item.content_type) }}</span>
                </div>
                <div class="picker-card-body">
                  <div class="picker-card-title">{{ item.title }}</div>
                  <div class="picker-card-meta">
                    <span>{{ contentTypeLabel(item.content_type) }}</span>
                    <span>{{ item.owner_name || '-' }}</span>
                  </div>
                  <a-tag v-if="isLibraryBound(item.id)" color="default" size="small">已关联</a-tag>
                  <a-tag v-else-if="isLibrarySelected(item.id)" color="blue" size="small">已选中</a-tag>
                </div>
              </div>
            </div>
            <a-empty v-else description="暂无资源" style="padding: 40px 0" />
          </a-spin>
        </div>
      </div>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, InboxOutlined } from '@ant-design/icons-vue'
import { getCourse } from '@/api/course'
import { getLibraryFolders, getLibraryItems } from '@/api/library'
import { bindTrainingResource, getTrainingResources, unbindTrainingResource } from '@/api/training'

const props = defineProps({
  trainingData: { type: Object, required: true },
  active: { type: Boolean, default: false },
  canManage: { type: Boolean, default: false },
})

const panelStyle = { background: '#fafafa', borderRadius: '6px', marginBottom: '8px', border: '1px solid #f0f0f0' }

// ===== 课程资源 =====
const linkedCourses = ref([])
const customCourses = computed(() => (props.trainingData.courses || []).filter(c => !c.courseId))
const expandedKeys = ref([])
let courseLoaded = false

// ===== 培训知识库资源 =====
const trainingResources = ref([])
const trainingResLoading = ref(false)
let trainingResLoaded = false
const removingRefId = ref(null)

// ===== 知识库选择弹窗 =====
const libraryModalVisible = ref(false)
const libraryConfirmLoading = ref(false)
const libraryLoading = ref(false)
const libraryItems = ref([])
const libraryFolders = ref([])
const librarySearch = ref('')
const selectedCategory = ref('all')
const selectedFolderId = ref(null)
const selectedLibraryIds = ref([])

const libraryCategories = [
  { key: 'all', label: '全部类型' },
  { key: 'video', label: '视频' },
  { key: 'document', label: '文档' },
  { key: 'image', label: '图片' },
  { key: 'audio', label: '音频' },
  { key: 'knowledge', label: '知识点' },
]

const boundLibraryItemIds = computed(() =>
  trainingResources.value
    .filter(r => r.binding_type === 'library_item' && r.library_item_id)
    .map(r => r.library_item_id)
)

// ===== 加载培训资源 =====
async function loadTrainingResources() {
  if (trainingResLoaded) return
  trainingResLoaded = true
  trainingResLoading.value = true
  try {
    trainingResources.value = await getTrainingResources(props.trainingData.id)
  } catch {
    trainingResources.value = []
    message.error('加载班级资源失败')
  } finally {
    trainingResLoading.value = false
  }
}

// ===== 加载知识库弹窗数据 =====
async function fetchLibraryFolders() {
  try {
    libraryFolders.value = await getLibraryFolders()
  } catch {
    libraryFolders.value = []
  }
}

async function fetchLibraryItems() {
  libraryLoading.value = true
  try {
    const params = {
      page: 1,
      size: -1,
      scope: 'private',
      search: librarySearch.value || undefined,
      folder_id: selectedFolderId.value || undefined,
    }
    if (selectedCategory.value !== 'all') {
      params.category = selectedCategory.value
    }
    const res = await getLibraryItems(params)
    libraryItems.value = res.items || []
  } catch {
    libraryItems.value = []
    message.error('加载知识库失败')
  } finally {
    libraryLoading.value = false
  }
}

watch(libraryModalVisible, async (val) => {
  if (!val) return
  selectedLibraryIds.value = []
  selectedCategory.value = 'all'
  selectedFolderId.value = null
  librarySearch.value = ''
  await Promise.all([fetchLibraryFolders(), fetchLibraryItems()])
})

function isLibrarySelected(id) {
  return selectedLibraryIds.value.includes(id)
}

function isLibraryBound(id) {
  return boundLibraryItemIds.value.includes(id)
}

function handleLibraryCardClick(event, item) {
  if (isLibraryBound(item.id)) return
  if (event.ctrlKey || event.metaKey) {
    if (isLibrarySelected(item.id)) {
      selectedLibraryIds.value = selectedLibraryIds.value.filter(id => id !== item.id)
    } else {
      selectedLibraryIds.value = [...selectedLibraryIds.value, item.id]
    }
    return
  }
  selectedLibraryIds.value = [item.id]
}

async function confirmLibraryAdd() {
  if (!selectedLibraryIds.value.length) {
    message.warning('请至少选择一个资源')
    return
  }
  libraryConfirmLoading.value = true
  let successCount = 0
  const errors = []

  for (const libraryItemId of selectedLibraryIds.value) {
    try {
      const result = await bindTrainingResource(props.trainingData.id, {
        library_item_id: libraryItemId,
        usage_type: 'required',
        sort_order: trainingResources.value.length,
      })
      trainingResources.value = [...trainingResources.value, result]
      successCount++
    } catch (e) {
      errors.push(e?.response?.data?.detail || e?.message || '绑定失败')
    }
  }

  libraryConfirmLoading.value = false
  libraryModalVisible.value = false

  if (successCount > 0) {
    message.success(`成功添加 ${successCount} 个知识库资源`)
  }
  if (errors.length) {
    message.error(`${errors.length} 个资源添加失败`)
  }
}

// ===== 移除培训资源 =====
function removeTrainingRes(res) {
  Modal.confirm({
    title: '移除资源',
    content: `确认移除「${res.title}」吗？`,
    okText: '确认移除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      removingRefId.value = res.ref_id
      try {
        await unbindTrainingResource(props.trainingData.id, res.ref_id)
        trainingResources.value = trainingResources.value.filter(r => r.ref_id !== res.ref_id)
        message.success('已移除')
      } catch (e) {
        message.error(e?.response?.data?.detail || '移除失败')
      } finally {
        removingRefId.value = null
      }
    },
  })
}

// ===== 加载课程资源 =====
async function loadCourseResources() {
  if (courseLoaded) return
  courseLoaded = true

  const courses = (props.trainingData.courses || []).filter(c => c.courseId)
  linkedCourses.value = courses.map(c => ({
    trainingCourse: c,
    chapters: [],
    loading: true,
  }))

  expandedKeys.value = courses.map(c => String(c.id))

  await Promise.all(
    linkedCourses.value.map(async (item) => {
      try {
        const detail = await getCourse(item.trainingCourse.courseId)
        item.chapters = (detail.chapters || []).slice().sort((a, b) => a.sortOrder - b.sortOrder)
      } catch {
        item.chapters = []
      } finally {
        item.loading = false
      }
    })
  )
}

async function loadAll() {
  await Promise.all([loadTrainingResources(), loadCourseResources()])
}

watch(
  () => props.active,
  (val) => { if (val) loadAll() },
  { immediate: true }
)

watch(
  () => props.trainingData?.id,
  () => {
    courseLoaded = false
    trainingResLoaded = false
    linkedCourses.value = []
    trainingResources.value = []
    if (props.active) loadAll()
  }
)

function boundChapterCount(item) {
  return item.chapters.filter(c => c.resourceId).length
}

function contentTypeIcon(type) {
  if (type === 'video') return '🎬'
  if (type === 'image') return '🖼️'
  if (type === 'audio') return '🎧'
  if (type === 'knowledge') return '🧠'
  return '📄'
}

function contentTypeLabel(type) {
  if (type === 'video') return '视频'
  if (type === 'image') return '图片'
  if (type === 'audio') return '音频'
  if (type === 'document') return '文档'
  if (type === 'knowledge') return '知识点'
  return type || '文件'
}

function contentTypeColor(type) {
  if (type === 'video') return 'purple'
  if (type === 'image') return 'cyan'
  if (type === 'knowledge') return 'green'
  return 'blue'
}
</script>

<style scoped>
.resources-content {
  padding: 0;
}

.res-section-block {
  padding: 4px 0;
}

.res-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.res-section-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.panel-title {
  font-weight: 600;
  font-size: 14px;
}

.resource-icon {
  margin-right: 6px;
}

/* ===== 已绑定资源列表 ===== */
.res-bound-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.res-bound-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafafa;
}

.res-type-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.res-bound-info {
  flex: 1;
  min-width: 0;
}

.res-bound-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.88);
  font-weight: 500;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.res-bound-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.res-bound-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* ===== 选择弹窗 ===== */
.picker-shell {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 16px;
  min-height: 500px;
}

.picker-sidebar {
  border-right: 1px solid #f0f0f0;
  padding-right: 16px;
}

.picker-side-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 8px;
}

.picker-side-block {
  margin-bottom: 12px;
}

.picker-category-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.picker-category-btn {
  border: none;
  background: transparent;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
  transition: all 0.2s;
}

.picker-category-btn:hover {
  background: rgba(22, 119, 255, 0.06);
  color: #1677ff;
}

.picker-category-btn.active {
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
  font-weight: 600;
}

.picker-folder-btn {
  padding: 7px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
  transition: all 0.2s;
  margin-bottom: 3px;
}

.picker-folder-btn:hover {
  background: rgba(22, 119, 255, 0.06);
  color: #1677ff;
}

.picker-folder-btn.active {
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
  font-weight: 600;
}

.picker-main {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.picker-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.picker-meta {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.picker-card {
  display: flex;
  gap: 10px;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.picker-card:hover {
  border-color: #d6e4ff;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.1);
}

.picker-card--selected {
  border-color: #4096ff;
  background: #f0f5ff;
}

.picker-card--bound {
  opacity: 0.6;
  cursor: not-allowed;
}

.picker-card-cover {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: #f5f5f5;
}

.cover-video { background: linear-gradient(135deg, #7c3aed, #4f46e5); }
.cover-document { background: linear-gradient(135deg, #0f766e, #0891b2); }
.cover-image { background: linear-gradient(135deg, #d97706, #f59e0b); }
.cover-audio { background: linear-gradient(135deg, #dc2626, #ec4899); }
.cover-knowledge { background: linear-gradient(135deg, #059669, #10b981); }

.picker-card-body {
  flex: 1;
  min-width: 0;
}

.picker-card-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.88);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.picker-card-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.45);
  flex-wrap: wrap;
  margin-bottom: 4px;
}
</style>

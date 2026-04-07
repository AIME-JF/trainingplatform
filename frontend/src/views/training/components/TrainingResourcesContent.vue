<template>
  <div class="resources-content">

    <!-- ===== 知识库资源 ===== -->
    <div class="res-section-block">
      <div class="res-section-header">
        <span class="res-section-title">知识库资源</span>
        <a-button type="primary" size="small" @click="libraryModalVisible = true">
          <PlusOutlined /> 添加知识库资源
        </a-button>
      </div>
      <a-empty description="暂无已添加的知识库资源" style="padding: 24px 0" />
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

    <a-divider style="margin: 12px 0" />

    <!-- ===== 班级资源 ===== -->
    <div class="res-section-block">
      <div class="res-section-header">
        <span class="res-section-title">班级资源</span>
        <a-button type="primary" size="small" @click="uploadModalVisible = true">
          <UploadOutlined /> 上传班级资源
        </a-button>
      </div>
      <a-empty description="暂无已上传的班级资源" style="padding: 24px 0" />
    </div>

    <!-- 知识库资源选择弹窗 -->
    <a-modal
      v-model:open="libraryModalVisible"
      title="选择知识库资源"
      ok-text="确认添加"
      cancel-text="取消"
      @ok="confirmLibraryAdd"
    >
      <a-input-search placeholder="搜索知识库资源名称" style="margin-bottom: 16px" />
      <a-empty description="知识库资源绑定功能开发中，敬请期待" style="padding: 24px 0" />
    </a-modal>

    <!-- 上传班级资源弹窗 -->
    <a-modal
      v-model:open="uploadModalVisible"
      title="上传班级资源"
      ok-text="确认上传"
      cancel-text="取消"
      @ok="confirmUpload"
    >
      <a-upload-dragger :before-upload="() => false" multiple style="margin-bottom: 8px">
        <p class="ant-upload-drag-icon"><InboxOutlined /></p>
        <p class="ant-upload-text">点击或拖拽文件到此区域</p>
        <p class="ant-upload-hint">支持文档、图片、视频等各类格式，班级资源上传功能开发中</p>
      </a-upload-dragger>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, InboxOutlined } from '@ant-design/icons-vue'
import { getCourse } from '@/api/course'

const props = defineProps({
  trainingData: { type: Object, required: true },
  active: { type: Boolean, default: false },
})

const panelStyle = { background: '#fafafa', borderRadius: '6px', marginBottom: '8px', border: '1px solid #f0f0f0' }

const linkedCourses = ref([])
const customCourses = computed(() => {
  return (props.trainingData.courses || []).filter(c => !c.courseId)
})

const expandedKeys = ref([])
let loaded = false

// 知识库资源弹窗
const libraryModalVisible = ref(false)
function confirmLibraryAdd() {
  message.success('知识库资源绑定功能开发中')
  libraryModalVisible.value = false
}

// 班级资源上传弹窗
const uploadModalVisible = ref(false)
function confirmUpload() {
  message.success('班级资源上传功能开发中')
  uploadModalVisible.value = false
}

async function loadResources() {
  if (loaded) return
  loaded = true

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

watch(
  () => props.active,
  (val) => { if (val) loadResources() },
  { immediate: true }
)

watch(
  () => props.trainingData?.id,
  () => {
    loaded = false
    linkedCourses.value = []
    if (props.active) loadResources()
  }
)

function boundChapterCount(item) {
  return item.chapters.filter(c => c.resourceId).length
}

function contentTypeIcon(type) {
  if (type === 'video') return '🎬'
  if (type === 'image') return '🖼️'
  return '📄'
}

function contentTypeLabel(type) {
  if (type === 'video') return '视频'
  if (type === 'image') return '图片'
  if (type === 'document') return '文档'
  return type || '文件'
}

function contentTypeColor(type) {
  if (type === 'video') return 'purple'
  if (type === 'image') return 'cyan'
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
</style>

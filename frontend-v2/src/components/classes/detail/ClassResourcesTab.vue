<template>
  <div>
    <a-modal
      v-model:open="previewVisible"
      :title="previewResource?.title || '资源预览'"
      :footer="null"
      :width="860"
      destroy-on-close
    >
      <div v-if="previewResource" class="resource-preview-body">
        <div class="resource-preview-meta">
          <a-tag :color="boundResourceStatusColor(previewResource)">
            {{ previewResource.status_label || previewResource.status || '资源库项' }}
          </a-tag>
          <span>{{ previewResource.uploader_name || '-' }}</span>
        </div>
        <div
          v-if="previewResource.content_type === 'knowledge'"
          class="resource-preview-html"
          v-html="previewResource.knowledge_content_html || '<p>暂无知识点内容</p>'"
        />
        <a-empty v-else description="当前资源暂无可内嵌预览内容" />
      </div>
    </a-modal>

    <a-empty
      v-if="linkedItems.length === 0 && customItems.length === 0 && !legacyResources.length && !loading"
      description="本班暂无可展示的课程资源"
    />

    <div v-else class="res-course-list">
      <div
        v-for="item in linkedItems"
        :key="item.trainingCourse.id"
        class="res-course-card"
      >
        <div class="res-course-top">
          <div class="res-course-info">
            <h4 class="res-course-name">{{ item.trainingCourse.name }}</h4>
            <div class="res-course-meta">
              <span class="res-badge res-badge--linked">已绑定课程</span>
              <span v-if="!item.loading" class="meta-hint">
                {{ item.courseResources.length }} 个课程关联资源 · {{ item.chapters.length }} 个章节 · {{ boundCount(item) }} 个章节绑定资源
              </span>
            </div>
          </div>
        </div>

        <div class="res-card-body">
          <div v-if="item.loading" class="res-loading">
            <a-spin size="small" /> 加载中…
          </div>

          <template v-else>
            <section v-if="item.courseResources.length" class="res-section">
              <div class="res-section-head">
                <h5>课程关联资源</h5>
                <span>这些资源会随课程继承到班级中</span>
              </div>
              <div class="res-linked-resource-list">
                <article
                  v-for="resource in item.courseResources"
                  :key="resource.ref_id || resource.id"
                  class="res-linked-resource-card"
                >
                  <div class="res-linked-resource-main">
                    <div class="res-linked-resource-top">
                      <span class="res-type-icon">{{ contentTypeIcon(resource.content_type) }}</span>
                      <strong>{{ resource.title }}</strong>
                      <a-tag :color="boundResourceStatusColor(resource)">{{ resource.status_label || resource.status || '-' }}</a-tag>
                    </div>
                    <div class="res-linked-resource-meta">
                      <span>类型：{{ contentTypeLabel(resource.content_type) }}</span>
                      <span>来源：{{ resource.source_label || (resource.binding_type === 'library_item' ? '个人资源库' : '公共资源') }}</span>
                      <span>上传者：{{ resource.uploader_name || '-' }}</span>
                      <span>归属部门：{{ resource.owner_department_name || '-' }}</span>
                    </div>
                    <div v-if="resource.tags?.length" class="res-linked-resource-tags">
                      <a-tag v-for="tag in resource.tags" :key="tag">{{ tag }}</a-tag>
                    </div>
                  </div>

                  <a-button type="link" class="res-view-link-btn" @click="openBoundResource(resource)">
                    查看资源
                  </a-button>
                </article>
              </div>
            </section>

            <section v-if="item.chapters.length" class="res-section">
              <div class="res-section-head">
                <h5>章节资源</h5>
                <span>课程章节中直接绑定的资源</span>
              </div>
              <div class="res-chapter-list">
                <div
                  v-for="ch in item.chapters"
                  :key="ch.id"
                  class="res-chapter-row"
                >
                  <span class="res-chapter-idx">{{ (ch.sort_order ?? 0) + 1 }}</span>
                  <span class="res-chapter-title">{{ ch.title }}</span>
                  <template v-if="ch.resource_id || ch.library_item_id">
                    <span class="res-chapter-resource">
                      <span class="res-type-icon">{{ contentTypeIcon(ch.content_type) }}</span>
                      {{ ch.resource_title || ch.resource_file_name || '未命名资源' }}
                    </span>
                    <span class="res-type-tag" :class="'res-type-' + (ch.content_type || 'document')">
                      {{ ch.resource_file_label || contentTypeLabel(ch.content_type) }}
                    </span>
                    <a
                      v-if="ch.file_url"
                      :href="ch.file_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="res-view-link"
                    >查看</a>
                    <span v-else class="res-na">—</span>
                  </template>
                  <template v-else>
                    <span class="res-chapter-resource res-na">未绑定资源</span>
                    <span class="res-na">—</span>
                    <span class="res-na">—</span>
                  </template>
                </div>
              </div>
            </section>

            <div v-if="!item.courseResources.length && !item.chapters.length" class="res-empty">
              该课程暂无可展示资源
            </div>
          </template>
        </div>
      </div>

      <div v-if="legacyResources.length" class="res-legacy-section">
        <div class="res-section-head">
          <h5>历史班级资源</h5>
          <span>兼容显示历史班级单独绑定的资源，当前不再支持新增</span>
        </div>
        <div class="res-linked-resource-list">
          <article
            v-for="resource in legacyResources"
            :key="resource.id"
            class="res-linked-resource-card"
          >
            <div class="res-linked-resource-main">
              <div class="res-linked-resource-top">
                <span class="res-type-icon">{{ contentTypeIcon(resource.content_type) }}</span>
                <strong>{{ resource.title }}</strong>
                <a-tag color="default">历史资源</a-tag>
              </div>
              <div class="res-linked-resource-meta">
                <span>类型：{{ contentTypeLabel(resource.content_type) }}</span>
                <span>上传者：{{ resource.uploader_name || '-' }}</span>
                <span>归属部门：{{ resource.owner_department_name || '-' }}</span>
              </div>
              <div v-if="resource.tags?.length" class="res-linked-resource-tags">
                <a-tag v-for="tag in resource.tags" :key="tag">{{ tag }}</a-tag>
              </div>
            </div>

            <a-button type="link" class="res-view-link-btn" @click="goResourceDetail(resource.id)">
              查看资源
            </a-button>
          </article>
        </div>
      </div>

      <div v-if="customItems.length > 0" class="res-custom-section">
        <div class="res-custom-label">以下课程为自定义课程，未继承课程资源</div>
        <div
          v-for="c in customItems"
          :key="c.id"
          class="res-custom-row"
        >
          <span class="res-custom-name">{{ c.name }}</span>
          <span class="res-badge res-badge--custom">自定义</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ChapterResponse } from '@/api/generated/model'
import type { CourseBoundResourceResponse, CourseResponse, ResourceListItemResponse } from '@/api/learning-resource'
import { getCourseDetail } from '@/api/learning-resource'

interface TrainingCourse {
  id: number
  name: string
  course_id?: number | null
  [key: string]: unknown
}

interface CourseResourceItem {
  trainingCourse: TrainingCourse
  courseResources: CourseBoundResourceResponse[]
  chapters: ChapterResponse[]
  loading: boolean
}

const props = withDefaults(defineProps<{
  courses: TrainingCourse[]
  active: boolean
  legacyResources?: ResourceListItemResponse[]
}>(), {
  legacyResources: () => [],
})

const router = useRouter()
const linkedItems = ref<CourseResourceItem[]>([])
const loading = ref(false)
const previewVisible = ref(false)
const previewResource = ref<CourseBoundResourceResponse | null>(null)
let loaded = false

const customItems = computed<TrainingCourse[]>(() =>
  props.courses.filter((course) => !course.course_id),
)

const legacyResources = computed(() => props.legacyResources || [])

function boundCount(item: CourseResourceItem): number {
  return item.chapters.filter((chapter) => chapter.resource_id || chapter.library_item_id).length
}

function contentTypeIcon(type?: string | null): string {
  if (type === 'video') return '🎬'
  if (type === 'image') return '🖼️'
  if (type === 'audio') return '🎧'
  if (type === 'knowledge') return '🧠'
  return '📄'
}

function contentTypeLabel(type?: string | null): string {
  if (type === 'video') return '视频'
  if (type === 'image') return '图片'
  if (type === 'audio') return '音频'
  if (type === 'knowledge') return '知识点'
  if (type === 'document') return '文档'
  return type || '文件'
}

function resourceStatusColor(status?: string | null) {
  const colorMap: Record<string, string> = {
    draft: 'default',
    pending_review: 'orange',
    reviewing: 'processing',
    published: 'green',
    rejected: 'red',
    offline: 'default',
  }
  return colorMap[status || ''] || 'default'
}

function boundResourceStatusColor(resource: CourseBoundResourceResponse) {
  if (resource.binding_type === 'library_item') {
    return resource.status === 'public' ? 'gold' : 'blue'
  }
  return resourceStatusColor(resource.status)
}

function goResourceDetail(resourceId: number) {
  void router.push(`/resource/detail/${resourceId}`)
}

function openBoundResource(resource: CourseBoundResourceResponse) {
  if (resource.binding_type === 'resource' && resource.resource_id) {
    void router.push(`/resource/detail/${resource.resource_id}`)
    return
  }
  if (resource.content_type === 'knowledge') {
    previewResource.value = resource
    previewVisible.value = true
    return
  }
  if (resource.file_url) {
    window.open(resource.file_url, '_blank', 'noopener,noreferrer')
    return
  }
  message.warning('当前资源暂无可预览内容')
}

async function loadResources() {
  if (loaded) return
  loaded = true
  loading.value = true

  const linked = props.courses.filter((course) => course.course_id)
  linkedItems.value = linked.map((course) => ({
    trainingCourse: course,
    courseResources: [],
    chapters: [],
    loading: true,
  }))

  await Promise.all(
    linkedItems.value.map(async (item) => {
      try {
        const detail = await getCourseDetail(item.trainingCourse.course_id!) as CourseResponse
        item.courseResources = [...(detail.resources || [])]
        item.chapters = (detail.chapters || []).slice().sort(
          (a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0),
        )
      } catch {
        item.courseResources = []
        item.chapters = []
      } finally {
        item.loading = false
      }
    }),
  )

  loading.value = false
}

watch(
  () => props.active,
  (active) => {
    if (active) {
      void loadResources()
    }
  },
  { immediate: true },
)

watch(
  () => props.courses,
  () => {
    loaded = false
    linkedItems.value = []
    if (props.active) {
      void loadResources()
    }
  },
)
</script>

<style scoped>
.res-course-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.res-course-card {
  border: 1px solid var(--v2-border-light);
  border-radius: var(--v2-radius);
  overflow: hidden;
}

.res-course-top {
  padding: 16px 18px;
  border-bottom: 1px solid var(--v2-border-light);
  background: linear-gradient(135deg, rgba(75, 110, 245, 0.04) 0%, transparent 100%);
}

.res-course-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 6px;
}

.res-course-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-hint {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.res-badge {
  display: inline-block;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 20px;
}

.res-badge--linked {
  background: rgba(52, 199, 89, 0.12);
  color: #22a854;
}

.res-badge--custom {
  background: var(--v2-bg);
  color: var(--v2-text-muted);
  border: 1px solid var(--v2-border-light);
}

.res-card-body {
  padding: 14px 18px 16px;
}

.res-section + .res-section {
  margin-top: 16px;
}

.res-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.res-section-head h5 {
  margin: 0;
  font-size: 14px;
  color: var(--v2-text-primary);
}

.res-section-head span {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.res-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--v2-text-muted);
  padding: 12px 0;
}

.res-empty {
  font-size: 13px;
  color: var(--v2-text-muted);
  padding: 12px 0;
  text-align: center;
}

.res-linked-resource-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.res-linked-resource-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  border: 1px solid var(--v2-border-light);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
}

.res-linked-resource-main {
  flex: 1;
  min-width: 0;
}

.res-linked-resource-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--v2-text-primary);
}

.res-linked-resource-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.res-linked-resource-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.res-view-link-btn {
  flex-shrink: 0;
  padding-inline: 0;
}

.res-chapter-list {
  display: flex;
  flex-direction: column;
}

.res-chapter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 4px;
  border-bottom: 1px solid var(--v2-border-light);
  font-size: 13px;
}

.res-chapter-row:last-child {
  border-bottom: none;
}

.res-chapter-idx {
  width: 24px;
  text-align: right;
  color: var(--v2-text-muted);
  font-size: 12px;
  flex-shrink: 0;
}

.res-chapter-title {
  flex: 1;
  min-width: 0;
  color: var(--v2-text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.res-chapter-resource {
  flex: 1;
  min-width: 0;
  color: var(--v2-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 5px;
}

.res-type-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.res-type-tag {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  flex-shrink: 0;
}

.res-type-video { background: rgba(114, 46, 209, 0.1); color: #722ed1; }
.res-type-image { background: rgba(19, 194, 194, 0.1); color: #08979c; }
.res-type-audio { background: rgba(245, 34, 45, 0.08); color: #cf1322; }
.res-type-knowledge { background: rgba(19, 194, 163, 0.1); color: #08979c; }
.res-type-document,
.res-type-mixed { background: rgba(75, 110, 245, 0.1); color: var(--v2-primary); }

.res-view-link {
  font-size: 12px;
  color: var(--v2-primary);
  flex-shrink: 0;
  text-decoration: none;
}

.res-view-link:hover {
  text-decoration: underline;
}

.res-na {
  color: var(--v2-text-muted);
  font-size: 12px;
  flex-shrink: 0;
}

.res-legacy-section,
.res-custom-section {
  padding: 16px 18px;
  border: 1px dashed var(--v2-border-light);
  border-radius: var(--v2-radius);
}

.res-custom-label {
  font-size: 12px;
  color: var(--v2-text-muted);
  margin-bottom: 10px;
}

.res-custom-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--v2-border-light);
}

.res-custom-row:last-child {
  border-bottom: none;
}

.res-custom-name {
  flex: 1;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.resource-preview-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-preview-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.resource-preview-html {
  max-height: 60vh;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--v2-border-light);
  border-radius: 12px;
  background: #fff;
  color: var(--v2-text-primary);
  line-height: 1.7;
}

@media (max-width: 768px) {
  .res-linked-resource-card,
  .res-course-top,
  .res-card-body {
    padding-inline: 14px;
  }

  .res-linked-resource-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .res-section-head {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 600px) {
  .res-chapter-resource {
    display: none;
  }
}
</style>

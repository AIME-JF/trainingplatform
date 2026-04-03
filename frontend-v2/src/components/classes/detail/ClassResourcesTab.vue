<template>
  <div>
    <a-empty v-if="linkedItems.length === 0 && !loading" description="本班暂无关联课程资源" />

    <div v-else class="res-course-list">
      <div
        v-for="item in linkedItems"
        :key="item.trainingCourse.id"
        class="res-course-card"
      >
        <!-- 课程头 -->
        <div class="res-course-top">
          <div class="res-course-info">
            <h4 class="res-course-name">{{ item.trainingCourse.name }}</h4>
            <div class="res-course-meta">
              <span class="res-badge res-badge--linked">已关联课程资源</span>
              <span v-if="!item.loading && item.chapters.length > 0" class="meta-hint">
                {{ item.chapters.length }} 个章节 · {{ boundCount(item) }} 个绑定资源
              </span>
            </div>
          </div>
        </div>

        <!-- 章节列表 -->
        <div class="res-chapter-body">
          <div v-if="item.loading" class="res-loading">
            <a-spin size="small" /> 加载中…
          </div>
          <div v-else-if="item.chapters.length === 0" class="res-empty">该课程暂无章节</div>
          <div v-else class="res-chapter-list">
            <div
              v-for="ch in item.chapters"
              :key="ch.id"
              class="res-chapter-row"
            >
              <span class="res-chapter-idx">{{ (ch.sort_order ?? 0) + 1 }}</span>
              <span class="res-chapter-title">{{ ch.title }}</span>
              <template v-if="ch.resource_id">
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
        </div>
      </div>

      <!-- 自定义课程 -->
      <div v-if="customItems.length > 0" class="res-custom-section">
        <div class="res-custom-label">以下课程为自定义课程，无章节资源</div>
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
import { ref, computed, watch } from 'vue'
import { getCourseApiV1CoursesCourseIdGet } from '@/api/generated/course-management/course-management'
import type { ChapterResponse } from '@/api/generated/model'

interface TrainingCourse {
  id: number
  name: string
  course_id?: number | null
  [key: string]: unknown
}

interface CourseResourceItem {
  trainingCourse: TrainingCourse
  chapters: ChapterResponse[]
  loading: boolean
}

const props = defineProps<{
  courses: TrainingCourse[]
  active: boolean
}>()

const linkedItems = ref<CourseResourceItem[]>([])
const loading = ref(false)
let loaded = false

const customItems = computed<TrainingCourse[]>(() =>
  props.courses.filter(c => !c.course_id)
)

function boundCount(item: CourseResourceItem): number {
  return item.chapters.filter(ch => ch.resource_id).length
}

function contentTypeIcon(type?: string | null): string {
  if (type === 'video') return '🎬'
  if (type === 'image') return '🖼️'
  return '📄'
}

function contentTypeLabel(type?: string | null): string {
  if (type === 'video') return '视频'
  if (type === 'image') return '图片'
  if (type === 'document') return '文档'
  return type || '文件'
}

async function loadResources() {
  if (loaded) return
  loaded = true

  const linked = props.courses.filter(c => c.course_id)
  linkedItems.value = linked.map(c => ({ trainingCourse: c, chapters: [], loading: true }))

  await Promise.all(
    linkedItems.value.map(async (item) => {
      try {
        const detail = await getCourseApiV1CoursesCourseIdGet(item.trainingCourse.course_id!)
        const raw = (detail as any)?.data ?? detail
        const chapters: ChapterResponse[] = (raw?.chapters || []).slice().sort(
          (a: ChapterResponse, b: ChapterResponse) => (a.sort_order ?? 0) - (b.sort_order ?? 0)
        )
        item.chapters = chapters
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
  () => props.courses,
  () => {
    loaded = false
    linkedItems.value = []
    if (props.active) loadResources()
  }
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
  background: linear-gradient(135deg, rgba(75,110,245,0.04) 0%, transparent 100%);
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

.res-chapter-body {
  padding: 12px 18px 8px;
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

.res-type-video   { background: rgba(114,46,209,0.1); color: #722ed1; }
.res-type-image   { background: rgba(19,194,194,0.1); color: #08979c; }
.res-type-document, .res-type-mixed { background: rgba(75,110,245,0.1); color: var(--v2-primary); }

.res-view-link {
  font-size: 12px;
  color: var(--v2-primary);
  flex-shrink: 0;
  text-decoration: none;
}

.res-view-link:hover { text-decoration: underline; }

.res-na {
  color: var(--v2-text-muted);
  font-size: 12px;
  flex-shrink: 0;
}

/* 自定义课程 */
.res-custom-section {
  margin-top: 8px;
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

.res-custom-row:last-child { border-bottom: none; }

.res-custom-name {
  flex: 1;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

@media (max-width: 600px) {
  .res-chapter-resource { display: none; }
}
</style>

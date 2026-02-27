<template>
  <div class="course-list-page">
    <div class="page-header">
      <h2>课程中心</h2>
      <a-button type="primary" v-if="authStore.isInstructor || authStore.isAdmin">
        <template #icon><PlusOutlined /></template>上传课程
      </a-button>
    </div>

    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索课程名称、关键词..." allow-clear />
        </a-col>
        <a-col :span="14">
          <div class="category-tabs">
            <a-tag
              v-for="cat in allCategories" :key="cat.value"
              :color="selectedCategory === cat.value ? 'blue' : 'default'"
              class="cat-tag" @click="selectedCategory = cat.value"
            >{{ cat.label }}</a-tag>
          </div>
        </a-col>
        <a-col :span="2" style="text-align:right">
          <a-select v-model:value="sortBy" size="small" style="width:100px">
            <a-select-option value="default">默认排序</a-select-option>
            <a-select-option value="rating">按评分</a-select-option>
            <a-select-option value="students">按学员数</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <div class="course-stats">
      共 <strong>{{ filteredCourses.length }}</strong> 门课程
      <span v-if="authStore.isStudent" style="margin-left:16px">
        已学 <strong style="color:var(--police-gold)">{{ completedCount }}</strong> 门 ·
        进行中 <strong style="color:#1890ff">{{ inProgressCount }}</strong> 门
      </span>
    </div>

    <div class="course-grid">
      <div v-for="course in filteredCourses" :key="course.id" class="course-card" @click="goDetail(course)">
        <div class="course-cover" :style="{ background: course.coverColor }">
          <div class="cover-icon">{{ getCoverIcon(course.category) }}</div>
          <div class="cover-badge" v-if="course.isRequired">
            <a-tag color="red" style="font-size:11px">必修</a-tag>
          </div>
          <div class="cover-duration">{{ formatDuration(course.duration) }}</div>
        </div>
        <div class="course-body">
          <div class="course-category">{{ getCategoryLabel(course.category) }}</div>
          <div class="course-title">{{ course.title }}</div>
          <div class="course-tags">
            <a-tag v-for="tag in course.tags.slice(0,2)" :key="tag" size="small">{{ tag }}</a-tag>
          </div>
          <div class="course-instructor">
            <a-avatar size="small" :style="{ background: '#003087', fontSize: '10px' }">{{ course.instructor.charAt(0) }}</a-avatar>
            <span class="instructor-name">{{ course.instructor }}</span>
            <span class="difficulty">
              <span v-for="i in 5" :key="i" :class="i <= course.difficulty ? 'star-filled' : 'star-empty'">★</span>
            </span>
          </div>
          <div v-if="authStore.isStudent" class="course-progress">
            <a-progress :percent="getCourseProgress(course.id)" :stroke-color="getCourseProgress(course.id) === 100 ? '#52c41a' : '#003087'" size="small" :show-info="false" />
            <span class="progress-text">{{ getCourseProgress(course.id) }}% 完成</span>
          </div>
          <div class="course-footer">
            <span><TeamOutlined /> {{ course.studentCount.toLocaleString() }} 人学过</span>
            <span class="rating"><StarFilled style="color:#faad14" /> {{ course.rating }}</span>
          </div>
        </div>
      </div>
    </div>
    <a-empty v-if="filteredCourses.length === 0" description="暂无符合条件的课程" style="margin-top:80px" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, TeamOutlined, StarFilled } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { MOCK_COURSES, COURSE_CATEGORIES } from '@/mock/courses'

const router = useRouter()
const authStore = useAuthStore()
const searchText = ref('')
const selectedCategory = ref('all')
const sortBy = ref('default')
const allCategories = [{ value: 'all', label: '全部' }, ...COURSE_CATEGORIES]

const filteredCourses = computed(() => {
  let list = [...MOCK_COURSES]
  if (searchText.value) list = list.filter(c => c.title.includes(searchText.value) || c.tags.some(t => t.includes(searchText.value)))
  if (selectedCategory.value !== 'all') list = list.filter(c => c.category === selectedCategory.value)
  if (sortBy.value === 'rating') list.sort((a, b) => b.rating - a.rating)
  if (sortBy.value === 'students') list.sort((a, b) => b.studentCount - a.studentCount)
  return list
})

const progressMap = { 1: 65, 2: 100, 3: 30, 4: 0, 5: 82, 6: 45 }
const getCourseProgress = (id) => progressMap[id] ?? 0
const completedCount = computed(() => Object.values(progressMap).filter(p => p === 100).length)
const inProgressCount = computed(() => Object.values(progressMap).filter(p => p > 0 && p < 100).length)
const getCategoryLabel = (cat) => COURSE_CATEGORIES.find(c => c.value === cat)?.label ?? cat
const formatDuration = (mins) => mins >= 60 ? `${Math.floor(mins/60)}h${mins%60>0?mins%60+'min':''}` : `${mins}min`
const coverIcons = { law: '⚖️', skill: '🔧', traffic: '🚗', community: '🏘️', cyber: '💻', physical: '💪' }
const getCoverIcon = (cat) => coverIcons[cat] ?? '📚'
const goDetail = (course) => router.push({ name: 'CourseDetail', params: { id: course.id } })
</script>

<style scoped>
.course-list-page { padding: 0; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-card { margin-bottom: 16px; }
.category-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-tag { cursor: pointer; font-size: 13px; padding: 2px 10px; border-radius: 12px; }
.course-stats { margin-bottom: 16px; color: #666; font-size: 13px; }
.course-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.course-card { background: #fff; border-radius: 8px; overflow: hidden; cursor: pointer; transition: all 0.25s; border: 1px solid #e8e8e8; }
.course-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,48,135,0.12); border-color: var(--police-primary); }
.course-cover { height: 140px; position: relative; display: flex; align-items: center; justify-content: center; }
.cover-icon { font-size: 48px; }
.cover-badge { position: absolute; top: 10px; left: 10px; }
.cover-duration { position: absolute; bottom: 8px; right: 10px; background: rgba(0,0,0,0.5); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.course-body { padding: 14px; }
.course-category { color: var(--police-primary); font-size: 11px; font-weight: 600; margin-bottom: 4px; }
.course-title { font-size: 15px; font-weight: 600; color: #1a1a1a; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.course-tags { margin-bottom: 10px; display: flex; gap: 4px; flex-wrap: wrap; }
.course-instructor { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.instructor-name { font-size: 12px; color: #666; flex: 1; }
.star-filled { color: #faad14; }
.star-empty { color: #ddd; }
.course-progress { margin-bottom: 10px; }
.progress-text { font-size: 11px; color: #888; }
.course-footer { display: flex; justify-content: space-between; font-size: 12px; color: #888; border-top: 1px solid #f0f0f0; padding-top: 10px; }
.rating { font-weight: 600; color: #333; }
</style>

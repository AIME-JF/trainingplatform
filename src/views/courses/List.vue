<template>
  <div class="course-list-page">
    <div class="page-header">
      <h2>课程中心</h2>
      <a-button type="primary" v-if="authStore.isInstructor || authStore.isAdmin" @click="openCreate">
        <template #icon><PlusOutlined /></template>上传课程
      </a-button>
    </div>

    <!-- ─── 上传 / 编辑 弹窗 ─── -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? '编辑课程' : '上传新课程'"
      :width="700"
      :footer="null"
      @cancel="closeModal"
      :destroy-on-close="true"
    >
      <a-steps :current="currentStep" size="small" style="margin:12px 0 24px">
        <a-step title="基本信息" description="名称、简介等" />
        <a-step title="章节管理" description="添加章节与媒体文件" />
      </a-steps>

      <!-- 步骤1：基本信息 -->
      <div v-show="currentStep === 0">
        <a-form :label-col="{ span: 5 }" style="padding-right:8px">
          <a-form-item label="课程名称" required>
            <a-input v-model:value="form.title" placeholder="请输入课程名称" />
          </a-form-item>
          <a-form-item label="课程分类" required>
            <a-select v-model:value="form.category" placeholder="选择分类" allow-clear style="width:100%">
              <a-select-option v-for="cat in COURSE_CATEGORIES.filter(c => c.key !== 'all')" :key="cat.key" :value="cat.key">
                {{ cat.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="课程简介">
            <a-textarea
              v-model:value="form.description"
              :rows="4"
              :max-length="500"
              show-count
              placeholder="请输入课程简介：学习目标、适用对象、主要内容..."
            />
          </a-form-item>
          <a-form-item label="授课教官">
            <a-input v-model:value="form.instructor" placeholder="请输入教官姓名" />
          </a-form-item>
          <a-form-item label="难度等级">
            <div style="display:flex;align-items:center;gap:12px">
              <a-rate v-model:value="form.difficulty" :count="5" />
              <span style="color:#888;font-size:12px">{{ difficultyLabel }}</span>
            </div>
          </a-form-item>
          <a-form-item label="课程标签">
            <a-select v-model:value="form.tags" mode="tags" placeholder="输入后回车添加标签" style="width:100%" />
          </a-form-item>
          <a-form-item label="是否必修">
            <a-switch v-model:checked="form.isRequired" />
          </a-form-item>
        </a-form>
      </div>

      <!-- 步骤2：章节管理 -->
      <div v-show="currentStep === 1" class="chapters-editor">
        <a-alert
          type="info"
          show-icon
          message="每个章节可单独上传对应的视频（MP4）或文档（PDF/PPT）文件，不同章节内容可以不同。"
          style="margin-bottom:16px;font-size:12px"
        />
        <div v-for="(ch, idx) in form.chapters" :key="idx" class="chapter-row">
          <div class="ch-header">
            <span class="ch-badge">第 {{ idx + 1 }} 章</span>
            <a-button
              v-if="form.chapters.length > 1"
              size="small"
              danger
              type="text"
              @click="removeChapter(idx)"
            >
              <template #icon><DeleteOutlined /></template>删除
            </a-button>
          </div>
          <a-row :gutter="10" style="margin-bottom:8px">
            <a-col :span="16">
              <a-input
                v-model:value="ch.title"
                :placeholder="`章节名称，如：第${idx+1}章：核心知识点`"
              />
            </a-col>
            <a-col :span="8">
              <a-input-number
                v-model:value="ch.duration"
                :min="5" :max="300"
                style="width:100%"
                addon-after="分钟"
              />
            </a-col>
          </a-row>
          <a-upload-dragger
            v-model:fileList="ch.fileList"
            :before-upload="() => false"
            :max-count="1"
            accept=".mp4,.pdf,.pptx,.ppt,.doc,.docx"
            class="chapter-upload"
          >
            <p><InboxOutlined style="font-size:26px;color:#003087" /></p>
            <p style="font-size:13px;font-weight:500;margin:4px 0">
              {{ ch.fileList.length ? '已选择文件，点击可更换' : '点击或拖拽上传此章节媒体文件' }}
            </p>
            <p style="font-size:11px;color:#aaa">MP4 视频 / PDF 文档 / PPT 课件，单文件 ≤ 500MB</p>
          </a-upload-dragger>
        </div>

        <a-button type="dashed" block @click="addChapter" style="margin-top:16px">
          <template #icon><PlusOutlined /></template>添加章节
        </a-button>
      </div>

      <!-- 弹窗自定义底部 -->
      <div class="modal-footer-btns">
        <a-button @click="closeModal">取消</a-button>
        <div style="display:flex;gap:8px">
          <a-button v-if="currentStep > 0" @click="currentStep--">上一步</a-button>
          <a-button v-if="currentStep < 1" type="primary" @click="goNextStep">下一步 →</a-button>
          <a-button v-if="currentStep === 1" type="primary" @click="handleSubmit">
            {{ editingId ? '保存修改' : '提交课程' }}
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- ─── 搜索 / 筛选 ─── -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索课程名称、关键词..." allow-clear />
        </a-col>
        <a-col :span="14">
          <div class="category-tabs">
            <a-tag
              v-for="cat in allCategories" :key="cat.key"
              :color="selectedCategory === cat.key ? 'blue' : 'default'"
              class="cat-tag" @click="selectedCategory = cat.key"
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

    <!-- ─── 课程卡片网格 ─── -->
    <div class="course-grid">
      <div v-for="course in filteredCourses" :key="course.id" class="course-card" @click="goDetail(course)">
        <div class="course-cover" :style="{ background: course.coverColor }">
          <div class="cover-icon">{{ getCoverIcon(course.category) }}</div>
          <div class="cover-type-badge">
            <a-tag :color="course.fileType === 'video' ? 'purple' : 'cyan'" style="font-size:10px;margin:0">
              {{ course.fileType === 'video' ? '🎬 视频' : '📄 文档' }}
            </a-tag>
          </div>
          <div class="cover-badge" v-if="course.isRequired">
            <a-tag color="red" style="font-size:11px">必修</a-tag>
          </div>
          <div class="cover-duration">{{ formatDuration(course.duration) }}</div>
          <!-- 管理员/教官的编辑按钮 -->
          <div
            v-if="authStore.isAdmin || authStore.isInstructor"
            class="cover-edit-btn"
            @click.stop="openEdit(course, $event)"
          >
            <EditOutlined /> 编辑
          </div>
        </div>
        <div class="course-body">
          <div class="course-category">{{ getCategoryLabel(course.category) }}</div>
          <div class="course-title">{{ course.title }}</div>
          <div class="course-tags">
            <a-tag v-for="tag in course.tags.slice(0, 2)" :key="tag" size="small">{{ tag }}</a-tag>
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
            <span class="rating"><StarFilled style="color:#faad14" /> {{ course.rating || '新课' }}</span>
          </div>
        </div>
      </div>
    </div>
    <a-empty v-if="filteredCourses.length === 0" description="暂无符合条件的课程" style="margin-top:80px" />
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, TeamOutlined, StarFilled, InboxOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { MOCK_COURSES, COURSE_CATEGORIES } from '@/mock/courses'

const router = useRouter()
const authStore = useAuthStore()
const searchText = ref('')
const selectedCategory = ref('all')
const sortBy = ref('default')
const allCategories = [{ key: 'all', label: '全部' }, ...COURSE_CATEGORIES]
const courseList = ref([...MOCK_COURSES])

// ─── 弹窗状态 ───
const modalVisible = ref(false)
const currentStep = ref(0)
const editingId = ref(null)

const form = reactive({
  title: '',
  category: null,
  description: '',
  instructor: '',
  difficulty: 3,
  tags: [],
  isRequired: false,
  chapters: [{ title: '', duration: 30, fileList: [] }],
})

const difficultyLabel = computed(() => {
  const labels = ['', '初级', '初中级', '中级', '中高级', '高级']
  return labels[Math.round(form.difficulty)] || ''
})

const resetForm = () => {
  form.title = ''
  form.category = null
  form.description = ''
  form.instructor = ''
  form.difficulty = 3
  form.tags = []
  form.isRequired = false
  form.chapters = [{ title: '', duration: 30, fileList: [] }]
}

const openCreate = () => {
  editingId.value = null
  currentStep.value = 0
  resetForm()
  modalVisible.value = true
}

const openEdit = (course, e) => {
  e?.stopPropagation()
  editingId.value = course.id
  currentStep.value = 0
  form.title = course.title
  form.category = course.category
  form.description = course.description || ''
  form.instructor = course.instructor || ''
  form.difficulty = course.difficulty || 3
  form.tags = [...(course.tags || [])]
  form.isRequired = !!course.isRequired
  form.chapters = (course.chapters || []).map(ch => ({
    title: ch.title,
    duration: ch.duration || 30,
    fileList: [],
  }))
  if (!form.chapters.length) form.chapters = [{ title: '', duration: 30, fileList: [] }]
  modalVisible.value = true
}

const closeModal = () => {
  modalVisible.value = false
  currentStep.value = 0
}

const goNextStep = () => {
  if (!form.title.trim()) return message.warning('请输入课程名称')
  if (!form.category) return message.warning('请选择课程分类')
  currentStep.value = 1
}

const addChapter = () => {
  form.chapters.push({ title: '', duration: 30, fileList: [] })
}

const removeChapter = (idx) => {
  form.chapters.splice(idx, 1)
}

const coverColors = ['#8B1A1A', '#003087', '#1a5c2e', '#6b3a8a', '#8b6914', '#2e4057', '#1a4a6b', '#3d1a5c']

const handleSubmit = () => {
  if (form.chapters.some(ch => !ch.title.trim())) {
    return message.warning('请填写所有章节名称')
  }

  let detectedFileType = 'video'
  const chapters = form.chapters.map((ch, idx) => {
    let videoUrl = ''
    let docUrl = ''
    if (ch.fileList.length > 0) {
      const f = ch.fileList[0].originFileObj || ch.fileList[0]
      if (f && f.name) {
        const ext = f.name.split('.').pop().toLowerCase()
        const isVid = ext === 'mp4'
        try {
          const blobUrl = URL.createObjectURL(f)
          if (isVid) videoUrl = blobUrl
          else docUrl = blobUrl
        } catch {}
        if (idx === 0) detectedFileType = isVid ? 'video' : 'document'
      }
    }
    return {
      id: `ch_${Date.now()}_${idx}`,
      title: ch.title,
      duration: ch.duration || 30,
      unlocked: idx === 0,
      progress: 0,
      ...(videoUrl ? { videoUrl } : {}),
      ...(docUrl ? { docUrl } : {}),
    }
  })

  const totalDuration = chapters.reduce((s, c) => s + c.duration, 0)
  const courseData = {
    id: editingId.value || `c${Date.now()}`,
    title: form.title,
    category: form.category,
    fileType: detectedFileType,
    description: form.description || '',
    instructor: form.instructor || '未指定',
    difficulty: form.difficulty,
    tags: form.tags.length ? form.tags : [getCategoryLabel(form.category)],
    isRequired: form.isRequired,
    categoryLabel: getCategoryLabel(form.category),
    chapters,
    chapterCount: chapters.length,
    duration: totalDuration,
    studentCount: 0,
    rating: 0,
    coverColor: coverColors[Math.floor(Math.random() * coverColors.length)],
    createDate: new Date().toISOString().split('T')[0],
    updateDate: new Date().toISOString().split('T')[0],
  }

  if (editingId.value) {
    const i = courseList.value.findIndex(c => c.id === editingId.value)
    if (i >= 0) courseList.value.splice(i, 1, courseData)
    message.success(`课程『${courseData.title}』修改成功`)
  } else {
    courseList.value.unshift(courseData)
    message.success(`课程『${courseData.title}』上传成功！`)
  }
  closeModal()
}

// ─── 列表 ───
const filteredCourses = computed(() => {
  let list = [...courseList.value]
  if (searchText.value) {
    list = list.filter(c => c.title.includes(searchText.value) || (c.tags || []).some(t => t.includes(searchText.value)))
  }
  if (selectedCategory.value !== 'all') list = list.filter(c => c.category === selectedCategory.value)
  if (sortBy.value === 'rating') list.sort((a, b) => b.rating - a.rating)
  if (sortBy.value === 'students') list.sort((a, b) => b.studentCount - a.studentCount)
  return list
})

const progressMap = { 'c001': 65, 'c002': 100, 'c003': 30, 'c004': 0, 'c005': 82, 'c006': 45 }
const getCourseProgress = (id) => progressMap[id] ?? 0
const completedCount = computed(() => Object.values(progressMap).filter(p => p === 100).length)
const inProgressCount = computed(() => Object.values(progressMap).filter(p => p > 0 && p < 100).length)
const getCategoryLabel = (cat) => COURSE_CATEGORIES.find(c => c.key === cat)?.label ?? cat
const formatDuration = (mins) => mins >= 60 ? `${Math.floor(mins / 60)}h${mins % 60 > 0 ? mins % 60 + 'min' : ''}` : `${mins}min`
const coverIcons = { law: '⚖️', fraud: '🔍', traffic: '🚗', community: '🏘️', cybersec: '💻', physical: '💪' }
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
.cover-type-badge { position: absolute; top: 10px; right: 10px; }
.cover-duration { position: absolute; bottom: 8px; right: 10px; background: rgba(0,0,0,0.5); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.cover-edit-btn {
  position: absolute; bottom: 8px; left: 10px;
  background: rgba(0,48,135,0.85); color: #fff;
  padding: 2px 10px; border-radius: 10px; font-size: 11px;
  opacity: 0; transition: opacity 0.2s; cursor: pointer;
}
.course-card:hover .cover-edit-btn { opacity: 1; }
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

/* 弹窗内章节编辑 */
.chapter-row {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
  background: #fafbfc;
}
.ch-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.ch-badge {
  background: var(--police-primary, #003087);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}
.chapter-upload :deep(.ant-upload.ant-upload-drag) {
  padding: 8px 0;
}
.modal-footer-btns {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 768px) {
  .course-grid { grid-template-columns: 1fr !important; }
  .filter-card :deep(.ant-card-body) { padding: 12px !important; }
  .page-header h2 { font-size: 18px !important; }
}
</style>

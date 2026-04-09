<template>
  <section class="page-content instructor-profile-page">
    <a-spin :spinning="loading">
      <div class="profile-container">
        <h1 class="page-title">教官信息采集</h1>

        <!-- 基本信息区 -->
        <div class="form-section">
          <h2 class="section-title">基本信息</h2>
          <div class="form-grid">
            <div class="form-item">
              <label>出生日期</label>
              <a-date-picker
                v-model:value="form.birth_date"
                placeholder="请选择出生日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </div>
            <div class="form-item">
              <label>籍贯</label>
              <a-input v-model:value="form.native_place" placeholder="请输入籍贯" />
            </div>
            <div class="form-item">
              <label>民族</label>
              <a-input v-model:value="form.ethnicity" placeholder="请输入民族" />
            </div>
            <div class="form-item">
              <label>学历</label>
              <a-select v-model:value="form.education" placeholder="请选择学历" allow-clear>
                <a-select-option value="高中">高中</a-select-option>
                <a-select-option value="大专">大专</a-select-option>
                <a-select-option value="本科">本科</a-select-option>
                <a-select-option value="硕士研究生">硕士研究生</a-select-option>
                <a-select-option value="博士研究生">博士研究生</a-select-option>
              </a-select>
            </div>
            <div class="form-item">
              <label>学位</label>
              <a-select v-model:value="form.degree" placeholder="请选择学位" allow-clear>
                <a-select-option value="学士">学士</a-select-option>
                <a-select-option value="硕士">硕士</a-select-option>
                <a-select-option value="博士">博士</a-select-option>
              </a-select>
            </div>
          </div>
        </div>

        <!-- 教官信息区 -->
        <div class="form-section">
          <h2 class="section-title">教官信息</h2>
          <div class="form-grid">
            <div class="form-item">
              <label>教官职称</label>
              <a-input v-model:value="form.instructor_title" placeholder="请输入教官职称" />
            </div>
            <div class="form-item">
              <label>岗位类型</label>
              <a-select v-model:value="form.position_type" placeholder="请选择岗位类型" allow-clear>
                <a-select-option value="专职">专职</a-select-option>
                <a-select-option value="兼职">兼职</a-select-option>
              </a-select>
            </div>
            <div class="form-item">
              <label>师资类型</label>
              <a-select v-model:value="form.teacher_type" placeholder="请选择师资类型" allow-clear>
                <a-select-option value="业务">业务</a-select-option>
                <a-select-option value="技能">技能</a-select-option>
              </a-select>
            </div>
            <div class="form-item">
              <label>教官等级</label>
              <a-select v-model:value="form.instructor_level" placeholder="请选择教官等级" allow-clear>
                <a-select-option value="高级">高级</a-select-option>
                <a-select-option value="中级">中级</a-select-option>
                <a-select-option value="初级">初级</a-select-option>
              </a-select>
            </div>
          </div>
        </div>

        <!-- 聘任信息区 -->
        <div class="form-section">
          <h2 class="section-title">聘任信息</h2>
          <div class="form-grid">
            <div class="form-item">
              <label>聘任开始日期</label>
              <a-date-picker
                v-model:value="form.appointment_start_date"
                placeholder="请选择开始日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </div>
            <div class="form-item">
              <label>聘任结束日期</label>
              <a-date-picker
                v-model:value="form.appointment_end_date"
                placeholder="请选择结束日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </div>
          </div>
        </div>

        <!-- 教学方向区 -->
        <div class="form-section">
          <h2 class="section-title">教学方向</h2>
          <div class="direction-tags">
            <a-checkable-tag
              v-for="dir in directionOptions"
              :key="dir.id"
              :checked="selectedDirectionIds.includes(dir.id)"
              @change="toggleDirection(dir.id)"
            >
              {{ dir.name }}
            </a-checkable-tag>
          </div>
          <a-empty v-if="!directionOptions.length" description="暂无可选教学方向" />
        </div>

        <!-- 授课经历区 -->
        <div class="form-section">
          <h2 class="section-title">
            授课经历
            <a-button type="primary" size="small" @click="openExpModal()">添加</a-button>
          </h2>
          <a-empty v-if="!experiences.length" description="暂无授课经历" />
          <div v-else class="experience-list">
            <div v-for="exp in experiences" :key="exp.id" class="experience-item">
              <div class="exp-header">
                <span class="exp-period">{{ exp.start_date }} ~ {{ exp.end_date }}</span>
                <span class="exp-actions">
                  <a-button type="link" size="small" @click="openExpModal(exp)">编辑</a-button>
                  <a-popconfirm title="确定删除该授课经历吗？" @confirm="deleteExperience(exp.id)">
                    <a-button type="link" size="small" danger>删除</a-button>
                  </a-popconfirm>
                </span>
              </div>
              <div class="exp-body">
                <div><strong>授课对象：</strong>{{ exp.target_audience }}</div>
                <div><strong>授课内容：</strong>{{ exp.content }}</div>
                <div v-if="exp.evaluation"><strong>评课情况：</strong>{{ exp.evaluation }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 教官简介区 -->
        <div class="form-section">
          <h2 class="section-title">教官简介</h2>
          <a-textarea
            v-model:value="form.instructor_intro"
            :rows="4"
            :maxlength="1000"
            show-count
            placeholder="请输入教官简介"
          />
        </div>

        <!-- 保存按钮 -->
        <div class="form-actions">
          <a-button type="primary" :loading="saving" @click="handleSave" block size="large">
            保存信息
          </a-button>
        </div>
      </div>
    </a-spin>

    <!-- 授课经历弹窗 -->
    <a-modal
      v-model:open="expModalVisible"
      :title="expEditingId ? '编辑授课经历' : '添加授课经历'"
      :confirm-loading="expSaving"
      ok-text="保存"
      @ok="handleSaveExp"
    >
      <a-form layout="vertical">
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="开始日期" required>
              <a-date-picker
                v-model:value="expForm.start_date"
                placeholder="请选择开始日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" required>
              <a-date-picker
                v-model:value="expForm.end_date"
                placeholder="请选择结束日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="授课对象" required>
          <a-input v-model:value="expForm.target_audience" placeholder="请输入授课对象" />
        </a-form-item>
        <a-form-item label="授课内容" required>
          <a-textarea v-model:value="expForm.content" :rows="3" placeholder="请输入授课内容" />
        </a-form-item>
        <a-form-item label="评课情况">
          <a-textarea v-model:value="expForm.evaluation" :rows="2" placeholder="请输入评课情况（选填）" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const userId = authStore.currentUser?.id

const loading = ref(false)
const saving = ref(false)

const form = reactive({
  birth_date: undefined as string | undefined,
  native_place: '',
  ethnicity: '',
  education: undefined as string | undefined,
  degree: undefined as string | undefined,
  instructor_title: '',
  position_type: undefined as string | undefined,
  teacher_type: undefined as string | undefined,
  instructor_level: undefined as string | undefined,
  appointment_start_date: undefined as string | undefined,
  appointment_end_date: undefined as string | undefined,
  instructor_intro: '',
})

// 教学方向
const directionOptions = ref<Array<{ id: number; name: string }>>([])
const selectedDirectionIds = ref<number[]>([])

function toggleDirection(id: number) {
  const idx = selectedDirectionIds.value.indexOf(id)
  if (idx >= 0) {
    selectedDirectionIds.value.splice(idx, 1)
  } else {
    selectedDirectionIds.value.push(id)
  }
}

// 授课经历
interface Experience {
  id: number
  start_date: string
  end_date: string
  target_audience: string
  content: string
  evaluation: string
}

const experiences = ref<Experience[]>([])
const expModalVisible = ref(false)
const expSaving = ref(false)
const expEditingId = ref<number | null>(null)
const expForm = reactive({
  start_date: undefined as string | undefined,
  end_date: undefined as string | undefined,
  target_audience: '',
  content: '',
  evaluation: '',
})

async function loadProfile() {
  if (!userId) return
  loading.value = true
  try {
    const res = await axiosInstance.get(`/users/${userId}`)
    const data = res.data as Record<string, unknown>
    form.birth_date = (data.birth_date as string) || undefined
    form.native_place = (data.native_place as string) || ''
    form.ethnicity = (data.ethnicity as string) || ''
    form.education = (data.education as string) || undefined
    form.degree = (data.degree as string) || undefined
    form.instructor_title = (data.instructor_title as string) || ''
    form.position_type = (data.position_type as string) || undefined
    form.teacher_type = (data.teacher_type as string) || undefined
    form.instructor_level = (data.instructor_level as string) || undefined
    form.appointment_start_date = (data.appointment_start_date as string) || undefined
    form.appointment_end_date = (data.appointment_end_date as string) || undefined
    form.instructor_intro = (data.instructor_intro as string) || ''
  } catch (e: unknown) {
    message.error((e as Error).message || '加载个人信息失败')
  } finally {
    loading.value = false
  }
}

async function loadDirectionOptions() {
  try {
    const res = await axiosInstance.get('/dict/teaching-directions', { params: { enabled: true } })
    directionOptions.value = (res.data as Array<{ id: number; name: string }>) || []
  } catch {
    directionOptions.value = []
  }
}

async function loadSelectedDirections() {
  if (!userId) return
  try {
    const res = await axiosInstance.get(`/instructors/${userId}/teaching-directions`)
    const items = (res.data as Array<{ id: number }>) || []
    selectedDirectionIds.value = items.map((d) => d.id)
  } catch {
    selectedDirectionIds.value = []
  }
}

async function loadExperiences() {
  if (!userId) return
  try {
    const res = await axiosInstance.get(`/instructors/${userId}/teaching-experiences`)
    experiences.value = (res.data as Experience[]) || []
  } catch {
    experiences.value = []
  }
}

async function handleSave() {
  if (!userId) return
  saving.value = true
  try {
    // 保存基本信息和教官信息
    await axiosInstance.put(`/users/${userId}`, {
      birth_date: form.birth_date || null,
      native_place: form.native_place || null,
      ethnicity: form.ethnicity || null,
      education: form.education || null,
      degree: form.degree || null,
      instructor_title: form.instructor_title || null,
      position_type: form.position_type || null,
      teacher_type: form.teacher_type || null,
      instructor_level: form.instructor_level || null,
      appointment_start_date: form.appointment_start_date || null,
      appointment_end_date: form.appointment_end_date || null,
      instructor_intro: form.instructor_intro || null,
    })

    // 保存教学方向
    await axiosInstance.put(`/instructors/${userId}/teaching-directions`, {
      direction_ids: selectedDirectionIds.value,
    })

    message.success('保存成功')
  } catch (e: unknown) {
    message.error((e as Error).message || '保存失败')
  } finally {
    saving.value = false
  }
}

function openExpModal(exp?: Experience) {
  if (exp) {
    expEditingId.value = exp.id
    expForm.start_date = exp.start_date
    expForm.end_date = exp.end_date
    expForm.target_audience = exp.target_audience
    expForm.content = exp.content
    expForm.evaluation = exp.evaluation || ''
  } else {
    expEditingId.value = null
    expForm.start_date = undefined
    expForm.end_date = undefined
    expForm.target_audience = ''
    expForm.content = ''
    expForm.evaluation = ''
  }
  expModalVisible.value = true
}

async function handleSaveExp() {
  if (!expForm.start_date || !expForm.end_date) {
    message.warning('请选择时间段')
    return
  }
  if (!expForm.target_audience.trim()) {
    message.warning('请输入授课对象')
    return
  }
  if (!expForm.content.trim()) {
    message.warning('请输入授课内容')
    return
  }
  expSaving.value = true
  try {
    const payload = {
      start_date: expForm.start_date,
      end_date: expForm.end_date,
      target_audience: expForm.target_audience.trim(),
      content: expForm.content.trim(),
      evaluation: expForm.evaluation.trim() || null,
    }
    if (expEditingId.value) {
      await axiosInstance.put(`/instructors/${userId}/teaching-experiences/${expEditingId.value}`, payload)
      message.success('更新成功')
    } else {
      await axiosInstance.post(`/instructors/${userId}/teaching-experiences`, payload)
      message.success('添加成功')
    }
    expModalVisible.value = false
    await loadExperiences()
  } catch (e: unknown) {
    message.error((e as Error).message || '保存失败')
  } finally {
    expSaving.value = false
  }
}

async function deleteExperience(id: number) {
  try {
    await axiosInstance.delete(`/instructors/${userId}/teaching-experiences/${id}`)
    message.success('删除成功')
    await loadExperiences()
  } catch (e: unknown) {
    message.error((e as Error).message || '删除失败')
  }
}

onMounted(() => {
  loadProfile()
  loadDirectionOptions()
  loadSelectedDirections()
  loadExperiences()
})
</script>

<style scoped>
.instructor-profile-page {
  background: linear-gradient(180deg, #eef4fb 0%, #f6f8fc 100%);
}

.profile-container {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 400;
  color: #172554;
  margin: 0 0 24px;
}

.form-section {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.78);
  border-radius: 16px;
  padding: 18px 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(43, 61, 108, 0.06);
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #172554;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  color: #666;
}

.direction-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.direction-tags :deep(.ant-tag-checkable) {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.experience-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.experience-item {
  padding: 12px 14px;
  background: #fafbfe;
  border-radius: 10px;
  border: 1px solid #eef1f6;
}

.exp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.exp-period {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.exp-actions {
  display: flex;
  gap: 4px;
}

.exp-body {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
}

.form-actions {
  margin-top: 8px;
  padding-bottom: 24px;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 16px 12px;
  }

  .page-title {
    text-align: center;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>

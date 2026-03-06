<template>
  <div class="instructor-list-page">
    <div class="page-header">
      <h2>教官库</h2>
      <a-button type="primary" v-if="authStore.isAdmin" @click="addVisible = true">
        <template #icon><PlusOutlined /></template>添加教官
      </a-button>
    </div>

    <!-- 添加教官弹窗 -->
    <a-modal v-model:open="addVisible" title="添加教官" @ok="handleAdd" okText="添加" cancelText="取消" :width="520">
      <a-form :label-col="{ span: 5 }" style="margin-top:16px">
        <a-form-item label="姓名"><a-input v-model:value="addForm.name" placeholder="请输入教官姓名" /></a-form-item>
        <a-form-item label="职级">
          <a-select v-model:value="addForm.title" placeholder="选择职级">
            <a-select-option value="高级教官">高级教官</a-select-option>
            <a-select-option value="中级教官">中级教官</a-select-option>
            <a-select-option value="初级教官">初级教官</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="单位"><a-input v-model:value="addForm.unit" placeholder="所属单位" /></a-form-item>
        <a-form-item label="专业方向"><a-select v-model:value="addForm.specialties" mode="tags" placeholder="输入后回车添加" /></a-form-item>
      </a-form>
    </a-modal>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索教官姓名、专业领域..." allow-clear />
        </a-col>
        <a-col :span="16">
          <div class="specialty-filter">
            <span style="color:#888;white-space:nowrap">专业方向：</span>
            <div class="specialty-tags">
              <a-tag v-for="s in specialtiesList" :key="s" :color="filterSpecialty === s ? 'blue' : 'default'" class="filter-tag" @click="filterSpecialty = s">{{ s }}</a-tag>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <div class="instructor-grid">
      <div v-for="inst in filteredInstructors" :key="inst.id" class="inst-card" @click="goDetail(inst)">
        <div class="inst-avatar-wrap">
          <a-avatar :size="72" :style="{ background: inst.avatarColor, fontSize: '28px' }">
            {{ inst.name.charAt(0) }}
          </a-avatar>
          <div class="inst-badge" :class="inst.level">{{ inst.levelLabel }}</div>
        </div>
        <div class="inst-name">{{ inst.name }}</div>
        <div class="inst-title">{{ inst.title }}</div>
        <div class="inst-unit">{{ inst.unit }}</div>

        <div class="inst-specialties">
          <a-tag v-for="s in inst.specialties.slice(0,2)" :key="s" size="small">{{ s }}</a-tag>
        </div>

        <div class="inst-stats">
          <div class="is-item">
            <div class="is-num">{{ inst.courseCount }}</div>
            <div class="is-label">课程数</div>
          </div>
          <div class="is-divider"></div>
          <div class="is-item">
            <div class="is-num">{{ inst.studentCount }}</div>
            <div class="is-label">培训人次</div>
          </div>
          <div class="is-divider"></div>
          <div class="is-item">
            <div class="is-num" style="color:#faad14">{{ inst.rating }}</div>
            <div class="is-label">评分</div>
          </div>
        </div>

        <div class="inst-card-actions" v-if="authStore.isAdmin" @click.stop>
          <a-popconfirm :title="`确定删除教官「${inst.name}」吗？`" ok-text="删除" cancel-text="取消" @confirm="deleteInstructor(inst)">
            <a-button size="small" type="text" danger><DeleteOutlined /> 删除</a-button>
          </a-popconfirm>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { MOCK_INSTRUCTORS } from '@/mock/instructors'

const router = useRouter()
const authStore = useAuthStore()
const searchText = ref('')
const filterSpecialty = ref('全部')

const instructorList = ref([...MOCK_INSTRUCTORS])

// 动态计算专业列表
const specialtiesList = computed(() => {
  const allS = new Set()
  instructorList.value.forEach(i => i.specialties.forEach(s => allS.add(s)))
  return ['全部', ...allS]
})

// 添加教官
const addVisible = ref(false)
const addForm = reactive({ name: '', title: undefined, unit: '', specialties: [] })
const avatarColors = ['#003087', '#c8a84b', '#8B1A1A', '#1a5c2e', '#6b3a8a', '#2e86de']
const levelMap = { '高级教官': { level: 'expert', label: '专家' }, '中级教官': { level: 'senior', label: '高级' }, '初级教官': { level: 'standard', label: '初级' } }

const handleAdd = () => {
  if (!addForm.name) return message.warning('请输入教官姓名')
  if (!addForm.title) return message.warning('请选择职级')
  const lv = levelMap[addForm.title] || { level: 'standard', label: '初级' }
  const newInst = {
    id: Date.now(),
    name: addForm.name,
    title: addForm.title,
    unit: addForm.unit || '未指定',
    specialties: addForm.specialties.length ? addForm.specialties : ['通用'],
    courseCount: 0,
    studentCount: 0,
    rating: 0,
    level: lv.level,
    levelLabel: lv.label,
    avatarColor: avatarColors[Math.floor(Math.random() * avatarColors.length)],
  }
  instructorList.value.unshift(newInst)
  addVisible.value = false
  Object.assign(addForm, { name: '', title: undefined, unit: '', specialties: [] })
  message.success('教官添加成功！')
}

const filteredInstructors = computed(() => {
  let list = [...instructorList.value]
  if (searchText.value) list = list.filter(i => i.name.includes(searchText.value) || i.specialties.some(s => s.includes(searchText.value)))
  if (filterSpecialty.value !== '全部') list = list.filter(i => i.specialties.includes(filterSpecialty.value))
  return list
})

const goDetail = (inst) => router.push({ name: 'InstructorDetail', params: { id: inst.id } })

function deleteInstructor(inst) {
  instructorList.value = instructorList.value.filter(i => i.id !== inst.id)
  message.success(`已删除教官「${inst.name}」`)
}
</script>

<style scoped>
.instructor-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-tag { cursor: pointer; }
.specialty-filter { display: flex; align-items: flex-start; gap: 8px; }
.specialty-tags { display: flex; flex-wrap: wrap; gap: 4px 0; }
.instructor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.inst-card { background: #fff; border-radius: 12px; border: 1px solid #e8e8e8; padding: 24px; text-align: center; cursor: pointer; transition: all 0.25s; }
.inst-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,48,135,0.12); border-color: var(--police-primary); }
.inst-avatar-wrap { position: relative; display: inline-block; margin-bottom: 12px; }
.inst-badge { position: absolute; bottom: 0; right: -4px; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; }
.inst-badge.senior { background: #c8a84b; color: #fff; }
.inst-badge.expert { background: #003087; color: #fff; }
.inst-badge.standard { background: #888; color: #fff; }
.inst-name { font-size: 18px; font-weight: 700; color: #1a1a1a; }
.inst-title { font-size: 13px; color: var(--police-primary); margin: 4px 0; }
.inst-unit { font-size: 12px; color: #888; margin-bottom: 12px; }
.inst-specialties { display: flex; justify-content: center; gap: 4px; flex-wrap: wrap; margin-bottom: 16px; }
.inst-stats { display: flex; align-items: center; justify-content: space-around; padding: 12px 0 0; border-top: 1px solid #f0f0f0; }
.is-item { text-align: center; }
.is-num { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.is-label { font-size: 11px; color: #888; }
.is-divider { width: 1px; height: 30px; background: #f0f0f0; }
.inst-card-actions { margin-top: 12px; padding-top: 8px; border-top: 1px solid #f0f0f0; text-align: right; }
</style>

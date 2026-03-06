<template>
  <div class="trainee-list-page">
    <div class="page-header">
      <h2>学员库</h2>
      <a-button type="primary" v-if="authStore.isAdmin" @click="addVisible = true">
        <template #icon><PlusOutlined /></template>添加学员
      </a-button>
    </div>

    <!-- 添加学员弹窗 -->
    <a-modal v-model:open="addVisible" title="添加学员" @ok="handleAdd" okText="添加" cancelText="取消" :width="520">
      <a-form :label-col="{ span: 5 }" style="margin-top:16px">
        <a-form-item label="姓名"><a-input v-model:value="addForm.name" placeholder="请输入学员姓名" /></a-form-item>
        <a-form-item label="等级">
          <a-select v-model:value="addForm.title" placeholder="选择等级">
            <a-select-option value="高级学员">高级学员</a-select-option>
            <a-select-option value="中级学员">中级学员</a-select-option>
            <a-select-option value="初级学员">初级学员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="单位"><a-input v-model:value="addForm.unit" placeholder="所属单位" /></a-form-item>
      </a-form>
    </a-modal>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-input-search v-model:value="searchText" placeholder="搜索学员姓名..." allow-clear />
        </a-col>
      </a-row>
    </a-card>

    <div class="trainee-grid">
      <div v-for="trainee in filteredTrainees" :key="trainee.id" class="traineecard" @click="goDetail(trainee)">
        <div class="traineeavatar-wrap">
          <a-avatar :size="72" :style="{ background: trainee.avatarColor, fontSize: '28px' }">
            {{ trainee.name.charAt(0) }}
          </a-avatar>
          <div class="traineebadge" :class="trainee.level">{{ trainee.levelLabel }}</div>
        </div>
        <div class="traineename">{{ trainee.name }}</div>
        <div class="traineetitle">{{ trainee.title }}</div>

        <div class="traineestats" style="margin-top: 16px;">
          <div class="is-item">
            <div class="is-num">{{ trainee.courseCount }}</div>
            <div class="is-label">课程数</div>
          </div>
          <div class="is-divider"></div>
          <div class="is-item">
            <div class="is-num" style="font-size: 14px;">{{ trainee.unit }}</div>
            <div class="is-label">所属单位</div>
          </div>
          <div class="is-divider"></div>
          <div class="is-item">
            <div class="is-num" style="color:#faad14">{{ trainee.rating }}</div>
            <div class="is-label">评分</div>
          </div>
        </div>

        <div class="trainee-card-actions" v-if="authStore.isAdmin" @click.stop>
          <a-popconfirm :title="`确定删除学员「${trainee.name}」吗？`" ok-text="删除" cancel-text="取消" @confirm="deleteTrainee(trainee)">
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
import { MOCK_TRAINEES } from '@/mock/trainees'

const router = useRouter()
const authStore = useAuthStore()
const searchText = ref('')

const traineeList = ref([...MOCK_TRAINEES])

// 添加学员
const addVisible = ref(false)
const addForm = reactive({ name: '', title: undefined, unit: '' })
const avatarColors = ['#003087', '#c8a84b', '#8B1A1A', '#1a5c2e', '#6b3a8a', '#2e86de']
const levelMap = { '高级学员': { level: 'expert', label: '专家' }, '中级学员': { level: 'senior', label: '高级' }, '初级学员': { level: 'standard', label: '初级' } }

const handleAdd = () => {
  if (!addForm.name) return message.warning('请输入学员姓名')
  if (!addForm.title) return message.warning('请选择等级')
  const lv = levelMap[addForm.title] || { level: 'standard', label: '初级' }
  const newTrainee = {
    id: Date.now(),
    name: addForm.name,
    title: addForm.title,
    unit: addForm.unit || '未指定',
    courseCount: 0,
    studentCount: 0,
    rating: 0,
    level: lv.level,
    levelLabel: lv.label,
    avatarColor: avatarColors[Math.floor(Math.random() * avatarColors.length)],
  }
  traineeList.value.unshift(newTrainee)
  addVisible.value = false
  Object.assign(addForm, { name: '', title: undefined, unit: '' })
  message.success('学员添加成功！')
}

const filteredTrainees = computed(() => {
  let list = [...traineeList.value]
  if (searchText.value) list = list.filter(i => i.name.includes(searchText.value))
  return list
})

const goDetail = (trainee) => router.push({ name: 'TraineeDetail', params: { id: trainee.id } })

function deleteTrainee(trainee) {
  traineeList.value = traineeList.value.filter(i => i.id !== trainee.id)
  message.success(`已删除学员「${trainee.name}」`)
}
</script>

<style scoped>
.trainee-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-tag { cursor: pointer; }
.trainee-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.traineecard { background: #fff; border-radius: 12px; border: 1px solid #e8e8e8; padding: 24px; text-align: center; cursor: pointer; transition: all 0.25s; }
.traineecard:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,48,135,0.12); border-color: var(--police-primary); }
.traineeavatar-wrap { position: relative; display: inline-block; margin-bottom: 12px; }
.traineebadge { position: absolute; bottom: 0; right: -4px; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; }
.traineebadge.senior { background: #c8a84b; color: #fff; }
.traineebadge.expert { background: #003087; color: #fff; }
.traineebadge.standard { background: #888; color: #fff; }
.traineename { font-size: 18px; font-weight: 700; color: #1a1a1a; }
.traineetitle { font-size: 13px; color: var(--police-primary); margin: 4px 0; }
.traineeunit { font-size: 12px; color: #888; margin-bottom: 12px; }
.traineespecialties { display: flex; justify-content: center; gap: 4px; flex-wrap: wrap; margin-bottom: 16px; }
.traineestats { display: flex; align-items: center; justify-content: space-around; padding: 12px 0 0; border-top: 1px solid #f0f0f0; }
.is-item { text-align: center; }
.is-num { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.is-label { font-size: 11px; color: #888; }
.is-divider { width: 1px; height: 30px; background: #f0f0f0; }
.trainee-card-actions { margin-top: 12px; padding-top: 8px; border-top: 1px solid #f0f0f0; text-align: right; }
</style>

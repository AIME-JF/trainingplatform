<template>
  <div class="plan-page">
    <div class="page-header">
      <h2>培训计划管理</h2>
      <a-space>
        <a-select v-model:value="filterYear" placeholder="培训年度" allow-clear style="width: 120px" @change="fetchList">
          <a-select-option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</a-select-option>
        </a-select>
        <a-input-search v-model:value="searchText" placeholder="搜索培训班名称" allow-clear style="width: 200px" @search="fetchList" />
        <a-button type="primary" @click="openCreate">新增</a-button>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data-source="list"
      :loading="loading"
      :pagination="pagination"
      row-key="id"
      :scroll="{ x: 1400 }"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'budget'">
          <span v-if="record.trainingCost">培训 {{ record.trainingCost }} 万</span>
          <span v-if="record.trainingCost && record.instructorCost"> / </span>
          <span v-if="record.instructorCost">师资 {{ record.instructorCost }} 万</span>
          <span v-if="!record.trainingCost && !record.instructorCost">—</span>
        </template>
        <template v-if="column.key === 'scale'">
          <span v-if="record.daysPerPeriod">{{ record.daysPerPeriod }}天/期</span>
          <span v-if="record.daysPerPeriod && record.totalPeriods"> × </span>
          <span v-if="record.totalPeriods">{{ record.totalPeriods }}期</span>
          <span v-if="!record.daysPerPeriod && !record.totalPeriods">—</span>
        </template>
        <template v-if="column.key === 'people'">
          <span v-if="record.participantCount">参训 {{ record.participantCount }}</span>
          <span v-if="record.participantCount && record.staffCount"> / </span>
          <span v-if="record.staffCount">工作 {{ record.staffCount }}</span>
          <span v-if="!record.participantCount && !record.staffCount">—</span>
        </template>
        <template v-if="column.key === 'action'">
          <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
          <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
            <a-button type="link" size="small" danger>删除</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <!-- 新增 / 编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? '编辑' : '新增'"
      :confirm-loading="saving"
      width="720px"
      @ok="handleSave"
    >
      <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="培训年度" required>
              <a-input v-model:value="form.year" placeholder="请输入培训年度" :maxlength="4" show-count />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="培训班名称" required>
              <a-input v-model:value="form.name" placeholder="请输入培训班名称" :maxlength="70" show-count />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="培训类别">
              <a-select v-model:value="form.category" placeholder="请选择培训类别" allow-clear>
                <a-select-option value="岗位培训">岗位培训</a-select-option>
                <a-select-option value="专题培训">专题培训</a-select-option>
                <a-select-option value="晋升培训">晋升培训</a-select-option>
                <a-select-option value="新警培训">新警培训</a-select-option>
                <a-select-option value="其他">其他</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="时间">
              <a-input v-model:value="form.timeInfo" placeholder="请输入时间" :maxlength="10" show-count />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="主办单位">
              <a-input v-model:value="form.organizer" placeholder="请输入主办单位" :maxlength="50" show-count />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="地点">
              <a-input v-model:value="form.location" placeholder="请输入地点" :maxlength="50" show-count />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="每期天数">
              <a-input-number v-model:value="form.daysPerPeriod" placeholder="请输入每期天数" :min="0" :max="999" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="合计期数">
              <a-input-number v-model:value="form.totalPeriods" placeholder="请输入合计期数" :min="0" :max="99" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="参训人数">
              <a-input-number v-model:value="form.participantCount" placeholder="请输入参训人数" :min="0" :max="9999" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="工作人员数">
              <a-input-number v-model:value="form.staffCount" placeholder="请输入工作人员数" :min="0" :max="99" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider orientation="left" plain>经费预算</a-divider>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="培训费用">
              <a-input-number v-model:value="form.trainingCost" placeholder="请输入培训费用" :min="0" style="width: 100%" addon-after="万元" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="师资费">
              <a-input-number v-model:value="form.instructorCost" placeholder="请输入师资费" :min="0" style="width: 100%" addon-after="万元" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="其他经费来源" :label-col="{ span: 3 }" :wrapper-col="{ span: 20 }">
          <a-input v-model:value="form.otherFunding" placeholder="请输入其他经费来源" :maxlength="10" show-count addon-after="万元" />
        </a-form-item>

        <a-divider />

        <a-form-item label="培训目的" :label-col="{ span: 3 }" :wrapper-col="{ span: 20 }">
          <a-textarea v-model:value="form.purpose" placeholder="请输入培训目的" :maxlength="200" show-count :rows="3" />
        </a-form-item>
        <a-form-item label="培训对象" :label-col="{ span: 3 }" :wrapper-col="{ span: 20 }">
          <a-textarea v-model:value="form.targetAudience" placeholder="请输入培训对象" :maxlength="200" show-count :rows="3" />
        </a-form-item>
        <a-form-item label="内容" :label-col="{ span: 3 }" :wrapper-col="{ span: 20 }">
          <a-textarea v-model:value="form.content" placeholder="请输入内容" :maxlength="200" show-count :rows="3" />
        </a-form-item>
        <a-form-item label="备注" :label-col="{ span: 3 }" :wrapper-col="{ span: 20 }">
          <a-textarea v-model:value="form.notes" placeholder="请输入备注" :maxlength="200" show-count :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  getTrainingPlans,
  createTrainingPlan,
  updateTrainingPlan,
  deleteTrainingPlan,
} from '@/api/trainingPlan'

const loading = ref(false)
const list = ref([])
const filterYear = ref(undefined)
const searchText = ref('')
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 5 }, (_, i) => String(currentYear - 2 + i))

const columns = [
  { title: '培训年度', dataIndex: 'year', key: 'year', width: 90 },
  { title: '培训班名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '培训类别', dataIndex: 'category', key: 'category', width: 100 },
  { title: '时间', dataIndex: 'timeInfo', key: 'timeInfo', width: 100 },
  { title: '主办单位', dataIndex: 'organizer', key: 'organizer', width: 120, ellipsis: true },
  { title: '地点', dataIndex: 'location', key: 'location', width: 120, ellipsis: true },
  { title: '规模', key: 'scale', width: 130 },
  { title: '人数', key: 'people', width: 150 },
  { title: '经费预算', key: 'budget', width: 180 },
  { title: '操作', key: 'action', width: 120, fixed: 'right' },
]

async function fetchList() {
  loading.value = true
  try {
    const result = await getTrainingPlans({
      page: pagination.current,
      size: pagination.pageSize,
      year: filterYear.value || undefined,
      search: searchText.value || undefined,
    })
    list.value = result.items || []
    pagination.total = result.total || 0
  } catch (e) {
    message.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchList()
}

// ── 弹窗 ──
const modalVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)

const emptyForm = () => ({
  year: String(currentYear),
  name: '',
  category: undefined,
  timeInfo: '',
  organizer: '',
  location: '',
  daysPerPeriod: undefined,
  totalPeriods: undefined,
  participantCount: undefined,
  staffCount: undefined,
  trainingCost: undefined,
  instructorCost: undefined,
  otherFunding: '',
  purpose: '',
  targetAudience: '',
  content: '',
  notes: '',
})

const form = reactive(emptyForm())

function resetForm() {
  Object.assign(form, emptyForm())
}

function openCreate() {
  editingId.value = null
  resetForm()
  modalVisible.value = true
}

function openEdit(record) {
  editingId.value = record.id
  Object.assign(form, {
    year: record.year,
    name: record.name,
    category: record.category || undefined,
    timeInfo: record.timeInfo || '',
    organizer: record.organizer || '',
    location: record.location || '',
    daysPerPeriod: record.daysPerPeriod,
    totalPeriods: record.totalPeriods,
    participantCount: record.participantCount,
    staffCount: record.staffCount,
    trainingCost: record.trainingCost != null ? Number(record.trainingCost) : undefined,
    instructorCost: record.instructorCost != null ? Number(record.instructorCost) : undefined,
    otherFunding: record.otherFunding || '',
    purpose: record.purpose || '',
    targetAudience: record.targetAudience || '',
    content: record.content || '',
    notes: record.notes || '',
  })
  modalVisible.value = true
}

async function handleSave() {
  if (!form.year || !form.name) {
    message.warning('请填写培训年度和培训班名称')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateTrainingPlan(editingId.value, form)
      message.success('更新成功')
    } else {
      await createTrainingPlan(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    await fetchList()
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteTrainingPlan(id)
    message.success('删除成功')
    await fetchList()
  } catch (e) {
    message.error(e.message || '删除失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.plan-page { padding: 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { margin: 0; color: #001234; }
</style>

<template>
  <div class="exam-manage-page">
    <div class="page-header">
      <h2>考试场次管理</h2>
      <a-button type="primary" @click="openCreateDrawer">
        <template #icon><PlusOutlined /></template>发布新考试
      </a-button>
    </div>

    <!-- 筛选 -->
    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input-search v-model:value="searchText" placeholder="搜索考试名称..." allow-clear @search="onSearch" />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterStatus" style="width:100%" @change="onFilterChange" placeholder="状态">
            <a-select-option value="all">全部状态</a-select-option>
            <a-select-option value="upcoming">即将开始</a-select-option>
            <a-select-option value="active">进行中</a-select-option>
            <a-select-option value="ended">已结束</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <!-- 考试列表 -->
    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :dataSource="examList"
        row-key="id"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        size="middle"
      >
        <template #bodyCell="slotProps">
          <div>
            <div v-if="slotProps.column.key === 'status'">
              <a-tag :color="slotProps.record.status === 'active' ? 'green' : slotProps.record.status === 'upcoming' ? 'orange' : 'default'">
                {{ slotProps.record.status === 'active' ? '进行中' : slotProps.record.status === 'upcoming' ? '即将开始' : '已结束' }}
              </a-tag>
            </div>
            <div v-else-if="slotProps.column.key === 'type'">
              {{ slotProps.record.type === 'formal' ? '正式' : '测验' }}
            </div>
            <div v-else-if="slotProps.column.key === 'time'" style="font-size: 12px; color: #666">
              {{ slotProps.record.startTime || '未设置' }}<br/>至<br/>{{ slotProps.record.endTime || '未设置' }}
            </div>
            <div v-else-if="slotProps.column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="openEditDrawer(slotProps.record)"><EditOutlined />设置</a-button>
              </a-space>
            </div>
          </div>
        </template>
      </a-table>
    </a-card>

    <!-- 发布/编辑 考试抽屉 -->
    <a-drawer
      v-model:open="drawerVisible"
      :title="isEdit ? '编辑考试' : '发布新考试'"
      width="680"
      @close="closeDrawer"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="考试名称" required>
              <a-input v-model:value="form.title" placeholder="如：2026年第一季度执法资格定级考试" />
            </a-form-item>
          </a-col>

          <a-col :span="8">
            <a-form-item label="考试类型">
              <a-select v-model:value="form.type">
                <a-select-option value="formal">正式考核</a-select-option>
                <a-select-option value="quiz">随堂测验</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="考试状态">
              <a-select v-model:value="form.status">
                <a-select-option value="upcoming">即将开始</a-select-option>
                <a-select-option value="active">进行中 (发布)</a-select-option>
                <a-select-option value="ended">已结束</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="参与范围">
              <a-input v-model:value="form.scope" placeholder="如：全体民警" />
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item label="起始与截止时间">
              <a-range-picker 
                v-model:value="dateRange" 
                show-time 
                format="YYYY-MM-DD HH:mm:ss" 
                value-format="YYYY-MM-DD HH:mm:ss" 
                style="width:100%" 
              />
            </a-form-item>
          </a-col>
          
          <a-col :span="6">
            <a-form-item label="考试时长(分钟)">
              <a-input-number v-model:value="form.duration" :min="10" :max="300" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="及格分数线">
              <a-input-number v-model:value="form.passingScore" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>

          <a-col :span="24">
            <a-form-item label="考试描述(选填)">
              <a-textarea v-model:value="form.description" :rows="3" />
            </a-form-item>
          </a-col>

          <a-col :span="24">
            <a-form-item label="配置试卷题目" required>
              <div class="selected-questions">
                <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
                  <span>已选 <strong>{{ form.questionIds.length }}</strong> 题，自动计算总分：<strong>{{ dynamicTotalScore }}</strong> 分</span>
                  <a-button type="primary" size="small" ghost @click="openQuestionPicker">从题库抽题</a-button>
                </div>
                <!-- 已选题目简略展示 -->
                <div v-if="selectedQuestionsCache.length > 0" class="q-cache-list">
                  <div class="q-cache-item" v-for="(item, i) in selectedQuestionsCache" :key="item.id">
                    <span class="q-cached-idx">{{ i + 1 }}.</span>
                    <span class="q-cached-type">[{{ item.type === 'single' ? '单选' : item.type === 'multi' ? '多选' : '判断' }}]</span>
                    <span class="q-cached-content">{{ item.content }}</span>
                    <span class="q-cached-score">{{ item.score || 2 }}分</span>
                    <a-button type="link" danger size="small" @click="removeSelectedQ(item.id)">移除</a-button>
                  </div>
                </div>
                <a-empty v-else description="暂未配置试卷题目" />
              </div>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      <template #footer>
        <a-space style="float:right">
          <a-button @click="closeDrawer">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="handleSave">保存考试配置</a-button>
        </a-space>
      </template>
    </a-drawer>

    <!-- 抽题 Modal -->
    <a-modal
      v-model:open="pickerVisible"
      title="从题库抽取题目"
      width="900px"
      @ok="confirmQuestionPick"
      @cancel="pickerVisible = false"
    >
      <div style="margin-bottom:16px;display:flex;gap:12px">
        <a-input-search v-model:value="qpSearch" placeholder="搜索题干" style="width: 250px" @search="loadPickerQ" />
        <a-select v-model:value="qpType" style="width: 120px" @change="loadPickerQ">
          <a-select-option value="all">所有题型</a-select-option>
          <a-select-option value="single">单选</a-select-option>
          <a-select-option value="multi">多选</a-select-option>
          <a-select-option value="judge">判断</a-select-option>
        </a-select>
        <a-select v-model:value="qpDiff" style="width: 120px" @change="loadPickerQ">
          <a-select-option value="all">所有难度</a-select-option>
          <a-select-option value="2">简单</a-select-option>
          <a-select-option value="3">中等</a-select-option>
          <a-select-option value="4">困难</a-select-option>
        </a-select>
        <span style="line-height:32px;color:var(--police-primary);margin-left:auto">
          本次勾选: {{ tempSelectedRowKeys.length }} 题
        </span>
      </div>

      <a-table
        :columns="qpColumns"
        :dataSource="qpList"
        row-key="id"
        :row-selection="qpRowSelection"
        :pagination="qpPagination"
        :loading="qpLoading"
        @change="handleQpTableChange"
        size="small"
        :scroll="{ y: 400 }"
      >
        <template #bodyCell="slotProps">
          <div v-if="slotProps.column.key === 'type'">
            {{ slotProps.record.type === 'single' ? '单选' : slotProps.record.type === 'multi' ? '多选' : '判断' }}
          </div>
        </template>
      </a-table>
    </a-modal>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, EditOutlined } from '@ant-design/icons-vue'
import { getExams, createExam, updateExam, getExamDetail } from '@/api/exam'
import { getQuestions } from '@/api/question'

// --- 列表区 ---
const searchText = ref('')
const filterStatus = ref('all')
const loading = ref(false)
const examList = ref([])

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const columns = [
  { title: '考试名称', dataIndex: 'title', key: 'title', width: 250, ellipsis: true },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '题目数', dataIndex: 'question_count', key: 'question_count', width: 80 },
  { title: '起止时间', key: 'time', width: 180 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' }
]

async function loadExams() {
  loading.value = true
  try {
    const res = await getExams({
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
      status: filterStatus.value !== 'all' ? filterStatus.value : undefined
    })
    examList.value = res.items || []
    pagination.total = res.total || 0
  } catch (e) {
    message.error('加载考试列表失败')
  } finally {
    loading.value = false
  }
}

function onSearch() { pagination.current = 1; loadExams() }
function onFilterChange() { pagination.current = 1; loadExams() }
function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadExams()
}

onMounted(() => {
  loadExams()
})

// --- 抽屉表单区 ---
const drawerVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)

const dateRange = ref(null)

const form = reactive({
  title: '',
  description: '',
  type: 'formal',
  status: 'upcoming',
  scope: '全体人员',
  duration: 60,
  passingScore: 60,
  questionIds: []
})

const selectedQuestionsCache = ref([]) // 存完整的题目对象用于显示

const dynamicTotalScore = computed(() => {
  return selectedQuestionsCache.value.reduce((acc, item) => acc + (item.score || 2), 0)
})

function resetForm() {
  form.title = ''
  form.description = ''
  form.type = 'formal'
  form.status = 'upcoming'
  form.scope = '全体人员'
  form.duration = 60
  form.passingScore = 60
  form.questionIds = []
  dateRange.value = null
  selectedQuestionsCache.value = []
}

function openCreateDrawer() {
  resetForm()
  isEdit.value = false
  editingId.value = null
  drawerVisible.value = true
}

async function openEditDrawer(record) {
  resetForm()
  isEdit.value = true
  editingId.value = record.id
  
  // 要获取完整的考试详情来拿到回显的题目列表
  const hide = message.loading('拉取考试配置中...', 0)
  try {
    const res = await getExamDetail(record.id)
    const detail = res.data || res
    
    form.title = detail.title
    form.description = detail.description || ''
    form.type = detail.type
    form.status = detail.status
    form.scope = detail.scope || ''
    form.duration = detail.duration || 60
    form.passingScore = detail.passing_score || 60
    
    if (detail.start_time && detail.end_time) {
      // 后端时间格式化可能带 T 和 Z，这里简化处理字符串
      dateRange.value = [
        detail.start_time.replace('T', ' ').substring(0, 19), 
        detail.end_time.replace('T', ' ').substring(0, 19)
      ]
    }
    
    if (detail.questions && Array.isArray(detail.questions)) {
      selectedQuestionsCache.value = detail.questions
      form.questionIds = detail.questions.map(q => q.id)
    }
    
    drawerVisible.value = true
  } catch (e) {
    message.error('拉取考试详情失败')
  } finally {
    hide()
  }
}

function closeDrawer() {
  drawerVisible.value = false
}

function removeSelectedQ(id) {
  form.questionIds = form.questionIds.filter(qid => qid !== id)
  selectedQuestionsCache.value = selectedQuestionsCache.value.filter(item => item.id !== id)
}

async function handleSave() {
  if (!form.title) return message.warning('请输入考试名称')
  if (form.questionIds.length === 0) return message.warning('请至少选择一道题目')
  if (!dateRange.value || dateRange.value.length !== 2) return message.warning('请设置考试起止时间')

  const payload = {
    title: form.title,
    description: form.description,
    type: form.type,
    status: form.status,
    scope: form.scope,
    duration: form.duration,
    passing_score: form.passingScore,
    total_score: dynamicTotalScore.value,
    start_time: dateRange.value[0], // 前端传递格式 YYYY-MM-DD HH:mm:ss
    end_time: dateRange.value[1],
    question_ids: form.questionIds
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      // 如果后端没有实现 updateExam, 可以用 create 替代或先不管。目前假设后端有
      // 注: 如果后端没有真正实现PUT路由，这里调updateExam可能会404，这取决于后端完善度
      // 我们暂用常规update/create调用处理
      try {
        await updateExam(editingId.value, payload)
        message.success('已更新考试配置')
      } catch (err) {
        // Fallback for backend potentially missing PUT endpoint
        if (err.response && err.response.status === 404) {
          message.warning('服务端未实现更新接口，这只是演示')
        } else {
          throw err
        }
      }
    } else {
      await createExam(payload)
      message.success('已发布新考试')
    }
    drawerVisible.value = false
    loadExams()
  } catch (e) {
    message.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// --- 题库选择 Modal ---
const pickerVisible = ref(false)
const qpSearch = ref('')
const qpType = ref('all')
const qpDiff = ref('all')
const qpLoading = ref(false)
const qpList = ref([])
const qpPagination = reactive({ current: 1, pageSize: 15, total: 0 })

// 由于分页表格选中的状态保留比较麻烦，这里用自定义缓存策略
// 但是作为演示，仅在这 1 页中选
const tempSelectedRowKeys = ref([])
const tempSelectedRowsMap = ref(new Map())

const qpColumns = [
  { title: '题干', dataIndex: 'content', key: 'content', ellipsis: true },
  { title: '题型', key: 'type', width: 80 },
  { title: '难度', dataIndex: 'difficulty', width: 80 }
]

const qpRowSelection = {
  selectedRowKeys: tempSelectedRowKeys,
  preserveSelectedRowKeys: true, 
  onChange: (keys, rows) => {
    tempSelectedRowKeys.value = keys
    rows.forEach(r => tempSelectedRowsMap.value.set(r.id, r))
  }
}

async function loadPickerQ() {
  qpLoading.value = true
  try {
    const res = await getQuestions({
      page: qpPagination.current,
      size: qpPagination.pageSize,
      search: qpSearch.value || undefined,
      type: qpType.value !== 'all' ? qpType.value : undefined,
      difficulty: qpDiff.value !== 'all' ? qpDiff.value : undefined
    })
    qpList.value = res.items || []
    qpPagination.total = res.total || 0
  } catch {
    message.error('拉取题库失败')
  } finally {
    qpLoading.value = false
  }
}

function handleQpTableChange(pag) {
  qpPagination.current = pag.current
  qpPagination.pageSize = pag.pageSize
  loadPickerQ()
}

function openQuestionPicker() {
  qpSearch.value = ''
  qpType.value = 'all'
  qpDiff.value = 'all'
  qpPagination.current = 1
  
  // 回显目前已经在表单里选的
  tempSelectedRowKeys.value = [...form.questionIds]
  tempSelectedRowsMap.value.clear()
  selectedQuestionsCache.value.forEach(item => {
    tempSelectedRowsMap.value.set(item.id, item)
  })
  
  loadPickerQ()
  pickerVisible.value = true
}

function confirmQuestionPick() {
  form.questionIds = [...tempSelectedRowKeys.value]
  selectedQuestionsCache.value = form.questionIds.map(id => tempSelectedRowsMap.value.get(id) || selectedQuestionsCache.value.find(item=>item.id===id))
  pickerVisible.value = false
  message.success(`已选中 ${form.questionIds.length} 道题目`)
}
</script>

<style scoped>
.exam-manage-page { padding: 0 }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }

.selected-questions {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
}

.q-cache-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.q-cache-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.q-cached-idx { color: #999; width: 20px; }
.q-cached-type { color: var(--police-primary); font-size: 12px; }
.q-cached-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.q-cached-score { color: #f5222d; font-weight: 600; font-size: 13px; width: 40px; text-align: right;}
</style>

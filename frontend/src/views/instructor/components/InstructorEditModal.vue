<template>
  <a-modal
    :open="open"
    title="编辑教官信息"
    ok-text="保存"
    cancel-text="取消"
    :confirm-loading="submitting"
    @ok="handleSubmit"
    @cancel="$emit('update:open', false)"
    width="640px"
  >
    <a-form layout="vertical" style="margin-top: 12px">
      <a-form-item label="教官职称">
        <a-input v-model:value="form.instructorTitle" placeholder="请输入教官职称" />
      </a-form-item>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="岗位类型">
            <a-select v-model:value="form.positionType" placeholder="请选择岗位类型" allow-clear>
              <a-select-option value="专职">专职</a-select-option>
              <a-select-option value="兼职">兼职</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="师资类型">
            <a-select v-model:value="form.teacherType" placeholder="请选择师资类型" allow-clear>
              <a-select-option value="业务">业务</a-select-option>
              <a-select-option value="技能">技能</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="教官等级">
            <a-select v-model:value="form.instructorLevel" placeholder="请选择教官等级" allow-clear>
              <a-select-option value="高级">高级</a-select-option>
              <a-select-option value="中级">中级</a-select-option>
              <a-select-option value="初级">初级</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="出生日期">
            <a-date-picker v-model:value="form.birthDate" placeholder="请选择出生日期" style="width: 100%" value-format="YYYY-MM-DD" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="聘任开始日期">
            <a-date-picker v-model:value="form.appointmentStartDate" placeholder="请选择开始日期" style="width: 100%" value-format="YYYY-MM-DD" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="聘任结束日期">
            <a-date-picker v-model:value="form.appointmentEndDate" placeholder="请选择结束日期" style="width: 100%" value-format="YYYY-MM-DD" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="籍贯">
            <a-input v-model:value="form.nativePlace" placeholder="请输入籍贯" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="民族">
            <a-input v-model:value="form.ethnicity" placeholder="请输入民族" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="学历">
            <a-select v-model:value="form.education" placeholder="请选择学历" allow-clear>
              <a-select-option value="高中">高中</a-select-option>
              <a-select-option value="大专">大专</a-select-option>
              <a-select-option value="本科">本科</a-select-option>
              <a-select-option value="硕士研究生">硕士研究生</a-select-option>
              <a-select-option value="博士研究生">博士研究生</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="学位">
            <a-select v-model:value="form.degree" placeholder="请选择学位" allow-clear>
              <a-select-option value="学士">学士</a-select-option>
              <a-select-option value="硕士">硕士</a-select-option>
              <a-select-option value="博士">博士</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="教官简介">
        <a-textarea
          v-model:value="form.instructorIntro"
          :rows="3"
          maxlength="1000"
          show-count
          placeholder="请输入教官简介"
        />
      </a-form-item>

      <a-divider orientation="left">教官标签</a-divider>
      <div v-for="(tag, idx) in form.tags" :key="idx" class="tag-row">
        <a-row :gutter="8" align="middle">
          <a-col :span="7">
            <a-select v-model:value="tag.adminLevel" placeholder="行政级别" style="width:100%">
              <a-select-option value="县级">县级</a-select-option>
              <a-select-option value="市级">市级</a-select-option>
              <a-select-option value="厅级">厅级</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="7">
            <a-select v-model:value="tag.professionalLevel" placeholder="专业等级" style="width:100%">
              <a-select-option value="初级">初级教官</a-select-option>
              <a-select-option value="中级">中级教官</a-select-option>
              <a-select-option value="高级">高级教官</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="8">
            <a-select
              v-model:value="tag.specialtyId"
              placeholder="专长方向"
              style="width:100%"
              show-search
              option-filter-prop="label"
            >
              <a-select-option v-for="s in specialtyOptions" :key="s.id" :value="s.id" :label="s.name">
                {{ s.name }}
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="2">
            <a-button type="link" danger @click="removeTag(idx)">删除</a-button>
          </a-col>
        </a-row>
      </div>
      <a-button type="dashed" block @click="addTag" style="margin-top: 8px">添加标签</a-button>
    </a-form>
  </a-modal>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import request from '@/api/request'

const props = defineProps({
  open: { type: Boolean, default: false },
  user: { type: Object, default: null },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'submit'])
const specialtyOptions = ref([])

const form = reactive({
  instructorTitle: '',
  instructorIntro: '',
  positionType: undefined,
  teacherType: undefined,
  instructorLevel: undefined,
  birthDate: undefined,
  appointmentStartDate: undefined,
  appointmentEndDate: undefined,
  nativePlace: '',
  ethnicity: '',
  education: undefined,
  degree: undefined,
  tags: [],
})

async function fetchSpecialties() {
  try {
    const data = await request.get('/dict/instructor-specialties', { params: { enabled: true } })
    specialtyOptions.value = data || []
  } catch {
    specialtyOptions.value = []
  }
}

function syncForm() {
  form.instructorTitle = props.user?.instructorTitle || ''
  form.instructorIntro = props.user?.instructorIntro || ''
  form.positionType = props.user?.positionType || undefined
  form.teacherType = props.user?.teacherType || undefined
  form.instructorLevel = props.user?.instructorLevel || undefined
  form.birthDate = props.user?.birthDate || undefined
  form.appointmentStartDate = props.user?.appointmentStartDate || undefined
  form.appointmentEndDate = props.user?.appointmentEndDate || undefined
  form.nativePlace = props.user?.nativePlace || ''
  form.ethnicity = props.user?.ethnicity || ''
  form.education = props.user?.education || undefined
  form.degree = props.user?.degree || undefined
  form.tags = (props.user?.instructorTags || []).map((t) => ({
    id: t.id,
    adminLevel: t.adminLevel,
    professionalLevel: t.professionalLevel,
    specialtyId: t.specialtyId,
  }))
}

function addTag() {
  form.tags.push({ adminLevel: undefined, professionalLevel: undefined, specialtyId: undefined })
}

function removeTag(idx) {
  form.tags.splice(idx, 1)
}

function handleSubmit() {
  emit('submit', {
    instructorTitle: form.instructorTitle || undefined,
    instructorIntro: form.instructorIntro || undefined,
    positionType: form.positionType || undefined,
    teacherType: form.teacherType || undefined,
    instructorLevel: form.instructorLevel || undefined,
    birthDate: form.birthDate || undefined,
    appointmentStartDate: form.appointmentStartDate || undefined,
    appointmentEndDate: form.appointmentEndDate || undefined,
    nativePlace: form.nativePlace || undefined,
    ethnicity: form.ethnicity || undefined,
    education: form.education || undefined,
    degree: form.degree || undefined,
    tags: form.tags.filter((t) => t.adminLevel && t.professionalLevel && t.specialtyId),
  })
}

watch(
  () => [props.open, props.user],
  () => {
    if (props.open) {
      syncForm()
      if (!specialtyOptions.value.length) fetchSpecialties()
    }
  },
  { immediate: true },
)

onMounted(fetchSpecialties)
</script>

<style scoped>
.tag-row {
  margin-bottom: 8px;
  padding: 8px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}
</style>

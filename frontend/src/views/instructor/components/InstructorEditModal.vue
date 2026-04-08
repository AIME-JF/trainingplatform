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

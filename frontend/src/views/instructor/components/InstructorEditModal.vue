<template>
  <a-modal
    :open="open"
    title="编辑教官信息"
    ok-text="保存"
    cancel-text="取消"
    :confirm-loading="submitting"
    @ok="handleSubmit"
    @cancel="$emit('update:open', false)"
  >
    <a-form layout="vertical" style="margin-top: 12px">
      <a-form-item label="教官职称">
        <a-input v-model:value="form.instructorTitle" placeholder="请输入教官职称" />
      </a-form-item>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="专业等级">
            <a-select v-model:value="form.instructorLevel" placeholder="选择专业等级" allow-clear>
              <a-select-option value="初级">初级教官</a-select-option>
              <a-select-option value="中级">中级教官</a-select-option>
              <a-select-option value="高级">高级教官</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="行政级别">
            <a-select v-model:value="form.instructorAdminLevel" placeholder="选择行政级别" allow-clear>
              <a-select-option value="县级">县级</a-select-option>
              <a-select-option value="市级">市级</a-select-option>
              <a-select-option value="厅级">厅级</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="教官资质">
            <a-select
              v-model:value="form.instructorQualification"
              mode="tags"
              allow-clear
              placeholder="可输入多个资质"
              style="width: 100%"
            />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="教官专长">
            <a-select
              v-model:value="form.instructorSpecialties"
              mode="tags"
              allow-clear
              placeholder="可输入多个专长"
              style="width: 100%"
            />
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="教官简介">
        <a-textarea
          v-model:value="form.instructorIntro"
          :rows="4"
          maxlength="1000"
          show-count
          placeholder="请输入教官简介"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  user: { type: Object, default: null },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'submit'])

const form = reactive({
  instructorTitle: '',
  instructorLevel: undefined,
  instructorAdminLevel: undefined,
  instructorQualification: [],
  instructorSpecialties: [],
  instructorIntro: '',
})

function syncForm() {
  form.instructorTitle = props.user?.instructorTitle || ''
  form.instructorLevel = props.user?.instructorLevel || undefined
  form.instructorAdminLevel = props.user?.instructorAdminLevel || undefined
  form.instructorQualification = [...(props.user?.instructorQualification || [])]
  form.instructorSpecialties = [...(props.user?.instructorSpecialties || [])]
  form.instructorIntro = props.user?.instructorIntro || ''
}

function handleSubmit() {
  emit('submit', {
    instructorTitle: form.instructorTitle || undefined,
    instructorLevel: form.instructorLevel || undefined,
    instructorAdminLevel: form.instructorAdminLevel || undefined,
    instructorQualification: form.instructorQualification.length ? form.instructorQualification : undefined,
    instructorSpecialties: form.instructorSpecialties.length ? form.instructorSpecialties : undefined,
    instructorIntro: form.instructorIntro || undefined,
  })
}

watch(
  () => [props.open, props.user],
  () => {
    if (props.open) {
      syncForm()
    }
  },
  { immediate: true },
)
</script>

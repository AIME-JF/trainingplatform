<template>
  <div class="schedule-rule-pane">
    <div class="section-header" style="margin-bottom:16px">
      <div>
        <h4 style="margin:0">排课规则</h4>
        <div class="section-helper">这里配置培训班默认排课规则。智能排课会优先读取这里的规则，任务页仅做少量临时覆盖。</div>
      </div>
      <permissions-tooltip :allowed="canEdit" :tips="editTooltip" v-slot="{ disabled }">
        <a-button type="primary" :disabled="disabled" :loading="saving" @click="handleSave">保存规则</a-button>
      </permissions-tooltip>
    </div>

    <a-alert
      type="info"
      show-icon
      style="margin-bottom:16px"
      message="系统默认规则会自动带入培训班。你可以在这里调整单课时、课间休息、时间段和默认排课方式。"
    />

    <a-form layout="vertical">
      <a-row :gutter="12">
        <a-col :span="6">
          <a-form-item label="单课时分钟数">
            <a-input-number v-model:value="form.lessonUnitMinutes" :min="20" :max="180" :disabled="!canEdit" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="课间休息分钟数">
            <a-input-number v-model:value="form.breakMinutes" :min="0" :max="60" :disabled="!canEdit" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="单节最多课时">
            <a-input-number v-model:value="form.maxUnitsPerSession" :min="1" :max="12" :disabled="!canEdit" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="单日最多课时">
            <a-input-number v-model:value="form.dailyMaxUnits" :min="1" :max="24" :disabled="!canEdit" style="width:100%" />
          </a-form-item>
        </a-col>
      </a-row>

      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="默认排课方式">
            <a-select v-model:value="form.preferredPlanningMode" :disabled="!canEdit">
              <a-select-option value="fill_workdays">排满工作日</a-select-option>
              <a-select-option value="fill_all_days">排满</a-select-option>
              <a-select-option value="by_hours">按课时排</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="拆分策略">
            <a-select v-model:value="form.splitStrategy" :disabled="!canEdit">
              <a-select-option value="balanced">尽量平分</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <div class="window-head">
        <div class="window-title">可排课时间段</div>
        <a-button v-if="canEdit" size="small" @click="addWindow">新增时间段</a-button>
      </div>
      <div v-if="form.teachingWindows.length" class="window-list">
        <div v-for="(window, index) in form.teachingWindows" :key="`${index}-${window.startTime}-${window.endTime}`" class="window-row">
          <a-input v-model:value="window.label" :maxlength="20" :disabled="!canEdit" placeholder="标签，如上午" style="width:160px" />
          <a-time-picker
            v-model:value="window.start"
            format="HH:mm"
            value-format="HH:mm"
            :disabled="!canEdit"
            placeholder="开始时间"
            style="width:140px"
          />
          <span class="window-separator">-</span>
          <a-time-picker
            v-model:value="window.end"
            format="HH:mm"
            value-format="HH:mm"
            :disabled="!canEdit"
            placeholder="结束时间"
            style="width:140px"
          />
          <a-button v-if="canEdit" type="link" danger @click="removeWindow(index)">删除</a-button>
        </div>
      </div>
      <a-empty v-else description="暂无可排课时间段" />
    </a-form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const props = defineProps({
  scheduleRuleConfig: { type: Object, default: () => ({}) },
  canEdit: { type: Boolean, default: false },
  editTooltip: { type: String, default: '' },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['save'])

const form = reactive({
  lessonUnitMinutes: 40,
  breakMinutes: 10,
  maxUnitsPerSession: 3,
  dailyMaxUnits: 6,
  preferredPlanningMode: 'fill_workdays',
  splitStrategy: 'balanced',
  teachingWindows: [],
})

function syncForm(value) {
  const source = value || {}
  form.lessonUnitMinutes = Number(source.lessonUnitMinutes || 40)
  form.breakMinutes = Number(source.breakMinutes || 10)
  form.maxUnitsPerSession = Number(source.maxUnitsPerSession || 3)
  form.dailyMaxUnits = Number(source.dailyMaxUnits || 6)
  form.preferredPlanningMode = source.preferredPlanningMode || 'fill_workdays'
  form.splitStrategy = source.splitStrategy || 'balanced'
  form.teachingWindows = (source.teachingWindows || []).map(item => ({
    label: item.label || '',
    start: item.startTime || item.start_time || '08:30',
    end: item.endTime || item.end_time || '12:30',
  }))
}

watch(
  () => props.scheduleRuleConfig,
  (value) => {
    syncForm(value)
  },
  { deep: true, immediate: true },
)

function addWindow() {
  form.teachingWindows.push({ label: '', start: '08:30', end: '12:30' })
}

function removeWindow(index) {
  form.teachingWindows.splice(index, 1)
}

function normalizePayload() {
  const teachingWindows = form.teachingWindows
    .map(item => ({
      label: String(item.label || '').trim(),
      startTime: item.start,
      endTime: item.end,
    }))
    .filter(item => item.startTime && item.endTime)

  return {
    lessonUnitMinutes: Number(form.lessonUnitMinutes || 40),
    breakMinutes: Number(form.breakMinutes || 0),
    maxUnitsPerSession: Number(form.maxUnitsPerSession || 1),
    dailyMaxUnits: Number(form.dailyMaxUnits || 1),
    preferredPlanningMode: form.preferredPlanningMode || 'fill_workdays',
    splitStrategy: form.splitStrategy || 'balanced',
    teachingWindows,
  }
}

function validatePayload(payload) {
  if (!payload.teachingWindows.length) {
    message.warning('请至少保留一个可排课时间段')
    return false
  }
  const invalidWindow = payload.teachingWindows.find(item => !item.startTime || !item.endTime || item.startTime >= item.endTime)
  if (invalidWindow) {
    message.warning('请检查时间段，结束时间必须晚于开始时间')
    return false
  }
  return true
}

function handleSave() {
  const payload = normalizePayload()
  if (!validatePayload(payload)) {
    return
  }
  emit('save', payload)
}
</script>

<style scoped>
.section-header { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; }
.section-helper { margin-top:8px; color:#64748b; font-size:12px; line-height:1.6; }
.window-head { display:flex; justify-content:space-between; align-items:center; margin:8px 0 12px; }
.window-title { font-weight:600; color:#0f172a; }
.window-list { display:flex; flex-direction:column; gap:12px; }
.window-row { display:flex; align-items:center; gap:12px; flex-wrap:wrap; padding:12px; border:1px solid #e2e8f0; border-radius:12px; background:#f8fafc; }
.window-separator { color:#64748b; }
</style>

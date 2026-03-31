<template>
  <div :data-tour-id="tourId('form')">
    <a-form layout="vertical">
      <slot name="top" />

      <div :data-tour-id="tourId('task-name')">
        <a-form-item label="任务名称" required>
          <a-input v-model:value="props.formState.taskName" placeholder="例：三月第二周排课建议" />
        </a-form-item>
      </div>

      <div :data-tour-id="tourId('training')">
        <a-form-item label="培训班" required>
          <a-select
            v-model:value="props.formState.trainingId"
            :options="props.trainingOptions"
            :disabled="props.disableTrainingSelect"
            placeholder="请选择培训班"
          />
        </a-form-item>
      </div>

      <a-row :gutter="12">
        <a-col :span="12">
          <div :data-tour-id="tourId('scope')">
            <a-form-item label="排课范围">
              <a-select v-model:value="props.formState.scopeType">
                <a-select-option value="all">全班次</a-select-option>
                <a-select-option value="current_week">指定周</a-select-option>
                <a-select-option value="unscheduled">仅未排课课次</a-select-option>
              </a-select>
            </a-form-item>
          </div>
        </a-col>
        <a-col :span="12">
          <div :data-tour-id="tourId('goal')">
            <a-form-item label="排课目标">
              <a-select v-model:value="props.formState.goal">
                <a-select-option value="balanced">均衡排课</a-select-option>
                <a-select-option value="practice_first">优先实战</a-select-option>
                <a-select-option value="theory_first">优先理论</a-select-option>
                <a-select-option value="exam_intensive">考前强化</a-select-option>
              </a-select>
            </a-form-item>
          </div>
        </a-col>
      </a-row>

      <a-row :gutter="12">
        <a-col :span="12">
          <div :data-tour-id="tourId('planning-mode')">
            <a-form-item label="排课方式">
              <a-select v-model:value="props.formState.planningMode">
                <a-select-option value="fill_workdays">排满工作日</a-select-option>
                <a-select-option value="fill_all_days">排满</a-select-option>
                <a-select-option value="by_hours">按课时排</a-select-option>
              </a-select>
              <div class="field-help">按课时排会严格使用课程计划课时；排满模式会优先铺满可排日期，不受计划课时限制。</div>
            </a-form-item>
          </div>
        </a-col>
        <a-col :span="12">
          <div :data-tour-id="tourId('daily-hours')">
            <a-form-item label="单日最大课时">
              <a-input-number v-model:value="props.formState.dailyMaxHours" :min="1" :max="12" style="width:100%" />
            </a-form-item>
          </div>
        </a-col>
      </a-row>

      <div v-if="props.formState.scopeType === 'current_week'" :data-tour-id="tourId('week')">
        <a-form-item label="指定周">
          <a-date-picker
            v-model:value="props.formState.scopeStartDate"
            style="width:100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            placeholder="请选择该周任意日期"
          />
          <div class="field-help">默认取培训周期内最近有效周，可修改；系统会自动按该周周一处理。</div>
        </a-form-item>
      </div>

      <div :data-tour-id="tourId('constraint')">
        <a-form-item>
          <a-checkbox v-model:checked="props.formState.avoidExamDays">避开考试日</a-checkbox>
        </a-form-item>
      </div>

      <a-form-item label="是否覆盖当前课表">
        <a-switch v-model:checked="props.formState.overwriteExistingSchedule" />
        <div class="field-help">
          关闭后会强制保留当前已有课次，并在最终保存和确认时校验不能误删或改动这些课次。
        </div>
      </a-form-item>

      <div :data-tour-id="tourId('notes')">
        <a-form-item label="补充说明">
          <a-textarea v-model:value="props.formState.notes" :rows="3" />
        </a-form-item>
      </div>

      <div class="more-toggle-row">
        <a-button type="link" class="more-toggle-button" @click="advancedExpanded = !advancedExpanded">
          {{ advancedExpanded ? '收起高级规则与约束' : '展开高级规则与约束' }}
        </a-button>
      </div>

      <div v-if="advancedExpanded">
        <div :data-tour-id="tourId('rule-overrides')">
          <a-divider orientation="left" plain>任务级规则覆盖</a-divider>
          <a-row :gutter="12">
            <a-col :span="6">
              <a-form-item label="单课时分钟数">
                <a-input-number v-model:value="props.formState.lessonUnitMinutes" :min="20" :max="180" style="width:100%" />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item label="课间休息分钟数">
                <a-input-number v-model:value="props.formState.breakMinutes" :min="0" :max="60" style="width:100%" />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item label="单节最多课时">
                <a-input-number v-model:value="props.formState.maxUnitsPerSession" :min="1" :max="12" style="width:100%" />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item label="拆分策略">
                <a-select value="balanced" disabled>
                  <a-select-option value="balanced">尽量平分</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="可排课时间段">
            <a-textarea
              v-model:value="props.formState.teachingWindowsText"
              :rows="3"
              placeholder="每行一个时间段，如：上午|08:30-12:30"
            />
            <div class="field-help">不填时默认使用培训班规则。支持写多行，格式如“上午|08:30-12:30”。</div>
          </a-form-item>
        </div>

        <div :data-tour-id="tourId('fixed-course-key')">
          <a-form-item label="固定课程键">
            <a-textarea v-model:value="props.formState.fixedCourseKeysText" :rows="2" placeholder="每行一个 course_key，可选" />
            <div class="field-help">填写需要锁定的 course_key。AI 生成建议时会保留这些已定课次，不再重新调整。</div>
          </a-form-item>
        </div>

        <a-divider orientation="left" plain>高级约束</a-divider>

        <a-form-item label="全局禁排时段">
          <a-textarea
            v-model:value="props.formState.blockedTimeSlotsText"
            :rows="3"
            placeholder="每行一条：日期|时间段|说明，例如 2026-03-25|14:00~17:30|周三下午不排课"
          />
          <div class="field-help">用于表达指定日期的全局禁排。规则解析阶段识别出的“周三下午不排课”这类约束也会落到这里。</div>
        </a-form-item>

        <a-form-item label="课程类型时段偏好">
          <a-textarea
            v-model:value="props.formState.courseTypePreferencesText"
            :rows="3"
            placeholder="每行一条：课程类型|开始~结束|星期1,2,3|prefer/only，例如 theory|08:30~12:30|1,2,3,4,5|only"
          />
          <div class="field-help">课程类型请填 theory 或 practice。prefer 表示优先，only 表示仅允许。</div>
        </a-form-item>

        <a-form-item label="教官不可用时段">
          <a-textarea
            v-model:value="props.formState.instructorUnavailableSlotsText"
            :rows="3"
            placeholder="每行一条：教官名|日期|时间段，例如 张三|2026-03-25|14:00~17:30"
          />
          <div class="field-help">只会限制同名教官的课程，不再全局误伤其他课次。</div>
        </a-form-item>

        <a-form-item label="场地不可用时段">
          <a-textarea
            v-model:value="props.formState.locationUnavailableSlotsText"
            :rows="3"
            placeholder="每行一条：场地名|日期|时间段，例如 靶场|2026-03-25|14:00~17:30"
          />
          <div class="field-help">只会限制同名场地的课程。</div>
        </a-form-item>

        <a-form-item label="考前强化偏好">
          <a-textarea
            v-model:value="props.formState.examWeekFocusText"
            :rows="2"
            placeholder="一行：提前天数|课程类型|关键词，例如 7|practice|警械,实战"
          />
          <div class="field-help">会优先把匹配课程排到考试前若干天，排不进去时会自动回退，不会把整个任务卡死。</div>
        </a-form-item>
      </div>

      <div :data-tour-id="tourId('create-button')">
        <a-button type="primary" block :loading="props.loading" @click="emit('submit')">
          {{ props.submitText }}
        </a-button>
      </div>
    </a-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  formState: {
    type: Object,
    required: true,
  },
  trainingOptions: {
    type: Array,
    default: () => [],
  },
  submitText: {
    type: String,
    default: '创建手动排课任务',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disableTrainingSelect: {
    type: Boolean,
    default: false,
  },
  tourPrefix: {
    type: String,
    default: 'schedule',
  },
})

const emit = defineEmits(['submit'])
const advancedExpanded = ref(false)

function tourId(name) {
  return `${props.tourPrefix}-${name}`
}
</script>

<style scoped>
.field-help { margin-top: 6px; color: #8c8c8c; font-size: 12px; line-height: 1.6; }
.more-toggle-row { display: flex; justify-content: center; margin: 4px 0 16px; }
.more-toggle-button { padding-inline: 0; }
</style>

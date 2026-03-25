<template>
  <div class="type-config-editor">
    <div class="editor-head">
      <div>
        <div class="editor-title">{{ title }}</div>
        <div class="editor-sub">{{ description }}</div>
      </div>
      <div class="editor-summary">
        <a-tag color="blue">共 {{ summary.totalCount }} 题</a-tag>
        <a-tag color="gold">预计 {{ summary.totalScore }} 分</a-tag>
      </div>
    </div>

    <div v-if="summary.totalCount === 0" class="editor-warning">
      至少保留一种题型数量大于 0。
    </div>

    <div class="config-table">
      <div class="config-head">
        <span>题型</span>
        <span>数量</span>
        <span>目标难度</span>
        <span>单题分值</span>
      </div>

      <div
        v-for="config in modelValue"
        :key="config.type"
        class="config-row"
      >
        <div class="config-type">
          <a-tag :color="typeColors[config.type] || 'default'">
            {{ typeLabels[config.type] || config.type }}
          </a-tag>
          <div class="config-subtotal">
            小计 {{ Number(config.count || 0) * Number(config.score || 0) }} 分
          </div>
        </div>

        <div class="config-field">
          <div class="field-label">数量</div>
          <a-input-number
            :value="resolveNumber(config.count, 0)"
            :min="0"
            :max="30"
            style="width: 100%;"
            @change="(value) => updateConfig(config.type, 'count', value, 0, true)"
          />
        </div>

        <div class="config-field">
          <div class="field-label">目标难度</div>
          <a-select
            :value="resolveNumber(config.difficulty, 3)"
            style="width: 100%;"
            @change="(value) => updateConfig(config.type, 'difficulty', value, 3)"
          >
            <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
              {{ difficultyLabels[level] }}
            </a-select-option>
          </a-select>
        </div>

        <div class="config-field">
          <div class="field-label">单题分值</div>
          <a-input-number
            :value="resolveNumber(config.score, 1)"
            :min="1"
            :max="20"
            style="width: 100%;"
            @change="(value) => updateConfig(config.type, 'score', value, 1)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { summarizePaperTypeConfigs } from '../utils/paperTypeConfig'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  title: { type: String, default: '题型配置' },
  description: { type: String, default: '请分别设置每种题型的数量、目标难度和单题分值。' },
})

const emit = defineEmits(['update:modelValue'])

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const difficultyLabels = { 1: '1级', 2: '2级', 3: '3级', 4: '4级', 5: '5级' }

const summary = computed(() => summarizePaperTypeConfigs(props.modelValue))

function resolveNumber(value, fallback) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : fallback
}

function updateConfig(type, key, value, fallback, allowZero = false) {
  const numericValue = Number(value)
  const nextValue = Number.isFinite(numericValue) && (allowZero ? numericValue >= 0 : numericValue > 0)
    ? numericValue
    : fallback
  const nextConfigs = (props.modelValue || []).map((item) => (
    item.type === type
      ? { ...item, [key]: nextValue }
      : { ...item }
  ))
  emit('update:modelValue', nextConfigs)
}
</script>

<style scoped>
.type-config-editor {
  border: 1px solid #eef0f5;
  border-radius: 12px;
  background: linear-gradient(180deg, #fbfcff 0%, #ffffff 100%);
  padding: 16px;
}

.editor-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.editor-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f1f1f;
}

.editor-sub {
  margin-top: 4px;
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.6;
}

.editor-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.editor-warning {
  margin-top: 12px;
  color: #cf1322;
  font-size: 12px;
}

.config-table {
  margin-top: 14px;
}

.config-head {
  display: grid;
  grid-template-columns: 160px repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 10px;
  padding: 0 4px;
  color: #8c8c8c;
  font-size: 12px;
}

.config-row {
  display: grid;
  grid-template-columns: 160px repeat(3, minmax(0, 1fr));
  gap: 12px;
  align-items: center;
  padding: 14px 12px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #f0f0f0;
}

.config-row + .config-row {
  margin-top: 10px;
}

.config-type {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-subtotal {
  color: #8c8c8c;
  font-size: 12px;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  color: #595959;
  font-size: 12px;
  line-height: 1;
}

@media (max-width: 768px) {
  .editor-head {
    flex-direction: column;
  }

  .config-head {
    display: none;
  }

  .config-row {
    grid-template-columns: 1fr;
  }
}
</style>

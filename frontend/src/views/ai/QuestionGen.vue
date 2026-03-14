<template>
  <div class="question-gen-page">
    <div class="page-header">
      <div>
        <h2>AI 智能组卷</h2>
        <p class="page-desc">基于知识库自动生成试题，支持多种题型和难度配置</p>
      </div>
      <a-tag color="blue">L3 智能体 · 题目生成</a-tag>
    </div>

    <a-row :gutter="20">
      <!-- 左侧配置 -->
      <a-col :span="10">
        <a-card title="生成配置" class="config-card">
          <a-form layout="vertical">
            <a-form-item label="知识范围（输入或粘贴文本）">
              <a-textarea
                v-model:value="inputText"
                placeholder="粘贴法规文本、案例材料或直接输入主题关键词，AI将据此生成题目..."
                :rows="6"
                :maxlength="2000"
                show-count
              />
            </a-form-item>

            <a-form-item label="快速选题（点击快速填充）">
              <div class="quick-topics">
                <a-tag v-for="t in quickTopics" :key="t" class="topic-tag" @click="inputText = t">{{ t }}</a-tag>
              </div>
            </a-form-item>

            <a-form-item label="生成题目数量">
              <a-slider v-model:value="config.count" :min="3" :max="20" :marks="countMarks" />
            </a-form-item>

            <a-form-item label="题型分布">
              <div class="type-config">
                <div class="type-row" v-for="type in typeConfig" :key="type.key">
                  <span class="type-label">{{ type.label }}</span>
                  <a-slider v-model:value="type.count" :min="0" :max="10" style="flex:1;margin:0 12px" />
                  <span class="type-count">{{ type.count }}题</span>
                </div>
              </div>
            </a-form-item>

            <a-form-item label="难度要求">
              <a-radio-group v-model:value="config.difficulty" button-style="solid">
                <a-radio-button value="easy">简单</a-radio-button>
                <a-radio-button value="medium">中等</a-radio-button>
                <a-radio-button value="hard">困难</a-radio-button>
                <a-radio-button value="mixed">混合</a-radio-button>
              </a-radio-group>
            </a-form-item>

            <a-button
              type="primary"
              block
              size="large"
              :loading="generating"
              @click="startGenerate"
              class="gen-btn"
            >
              <template #icon><ThunderboltOutlined /></template>
              {{ generating ? '生成中...' : '开始生成' }}
            </a-button>
          </a-form>
        </a-card>
      </a-col>

      <!-- 右侧结果 -->
      <a-col :span="14">
        <!-- 空状态 -->
        <div v-if="!generating && generatedQuestions.length === 0" class="empty-state">
          <div class="ai-idle">
            <div class="brain-icon">🧠</div>
            <p class="idle-title">AI 等待指令</p>
            <p class="idle-desc">配置左侧参数后，点击"开始生成"</p>
            <div class="feature-list">
              <div class="feature-item" v-for="f in features" :key="f.text">
                <span class="f-icon">{{ f.icon }}</span>
                <span>{{ f.text }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 生成中动画 -->
        <div v-if="generating" class="generating-state">
          <div class="gen-animation">
            <div class="brain-pulse">🧠</div>
            <div class="wave-bars">
              <div v-for="i in 5" :key="i" class="wave-bar" :style="{ animationDelay: i*0.15 + 's' }"></div>
            </div>
          </div>
          <p class="gen-status">{{ genStatus }}</p>
          <a-progress :percent="genProgress" :stroke-color="{ from: '#003087', to: '#c8a84b' }" status="active" />
          <div class="gen-steps">
            <div v-for="(step, i) in genSteps" :key="i" :class="['gen-step', step.done ? 'done' : step.active ? 'active' : '']">
              <span class="step-icon">{{ step.done ? '✅' : step.active ? '⏳' : '○' }}</span>
              {{ step.label }}
            </div>
          </div>
        </div>

        <!-- 生成结果 -->
        <div v-if="!generating && generatedQuestions.length > 0" class="result-state">
          <div class="result-header">
            <div>
              <span class="result-count">已生成 {{ generatedQuestions.length }} 道题目</span>
              <a-tag color="green" style="margin-left:8px">生成成功</a-tag>
            </div>
            <div class="result-actions">
              <a-button size="small" @click="generatedQuestions = []">重新生成</a-button>
              <a-button size="small" type="primary" @click="saveToBank">保存到题库</a-button>
            </div>
          </div>

          <div class="question-list">
            <div
              v-for="(q, idx) in generatedQuestions"
              :key="idx"
              class="q-item"
            >
              <div class="q-header" @click="q.expanded = !q.expanded">
                <div class="q-meta">
                  <a-tag :color="typeColors[q.type]" size="small">{{ typeLabels[q.type] }}</a-tag>
                  <span class="q-num">第 {{ idx+1 }} 题</span>
                </div>
                <div class="q-confidence">
                  <span class="conf-label">置信度</span>
                  <div class="conf-circle" :style="{ '--conf': q.confidence }">
                    {{ Math.round(q.confidence * 100) }}%
                  </div>
                </div>
              </div>

              <div class="q-content">{{ q.stem }}</div>

              <div class="q-options" v-if="q.options">
                <div v-for="(opt, oi) in q.options" :key="oi" class="q-option">
                  <span class="opt-label">{{ String.fromCharCode(65+oi) }}.</span> {{ opt }}
                </div>
              </div>

              <div class="q-source">
                <InfoCircleOutlined style="color:#aaa;margin-right:4px" />
                来源：{{ q.source }}
              </div>

              <div v-if="q.expanded" class="q-answer">
                <a-divider style="margin:8px 0" />
                <div class="answer-line">
                  <span class="ans-label">正确答案：</span>
                  <span class="ans-value">{{ q.answer }}</span>
                </div>
                <div class="ans-explain">{{ q.explanation }}</div>
                <div class="ai-note">
                  <RobotOutlined style="color:var(--police-primary)" /> {{ q.aiNote }}
                </div>
              </div>

              <div class="q-toggle" @click="q.expanded = !q.expanded">
                {{ q.expanded ? '▲ 收起答案' : '▼ 查看答案' }}
              </div>
            </div>
          </div>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { ThunderboltOutlined, InfoCircleOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { MOCK_AI_GENERATED_QUESTIONS } from '@/mock/ai-questions'

const inputText = ref('')
const generating = ref(false)
const genProgress = ref(0)
const genStatus = ref('')
const generatedQuestions = ref([])

const config = reactive({ count: 10, difficulty: 'mixed' })
const typeConfig = reactive([
  { key: 'single', label: '单选题', count: 5 },
  { key: 'multi', label: '多选题', count: 3 },
  { key: 'judge', label: '判断题', count: 2 },
])

const countMarks = { 3: '3', 5: '5', 10: '10', 15: '15', 20: '20' }

const quickTopics = [
  '《刑事诉讼法》第79条（逮捕条件）',
  '电信网络诈骗案件取证规范',
  '行政执法中的当场处罚程序',
  '警察盘问与留置的法律界限',
  '现场勘验的程序与注意事项',
]

const features = [
  { icon: '⚡', text: '秒级生成，支持最多20题' },
  { icon: '🎯', text: '自动提取关键知识点' },
  { icon: '📊', text: '多维度难度评估' },
  { icon: '📝', text: '一键导出到题库' },
]

const genSteps = reactive([
  { label: '分析输入文本', done: false, active: false },
  { label: '提取核心知识点', done: false, active: false },
  { label: '生成题干与选项', done: false, active: false },
  { label: '验证题目质量', done: false, active: false },
  { label: '生成完成', done: false, active: false },
])

const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }

const startGenerate = () => {
  if (!inputText.value.trim()) {
    message.warning('请输入知识范围或选择快捷主题')
    return
  }
  generating.value = true
  genProgress.value = 0
  genSteps.forEach(s => { s.done = false; s.active = false })

  const steps = [
    { idx: 0, label: '正在分析输入文本...', prog: 20, delay: 0 },
    { idx: 1, label: '提取核心知识点...', prog: 40, delay: 800 },
    { idx: 2, label: '生成题干与选项...', prog: 70, delay: 1800 },
    { idx: 3, label: '质量验证中...', prog: 90, delay: 3000 },
    { idx: 4, label: '生成完成！', prog: 100, delay: 3800 },
  ]

  steps.forEach(({ idx, label, prog, delay }) => {
    setTimeout(() => {
      genStatus.value = label
      genProgress.value = prog
      if (idx > 0) genSteps[idx-1].active = false, genSteps[idx-1].done = true
      genSteps[idx].active = true
    }, delay)
  })

  setTimeout(() => {
    genSteps[4].active = false
    genSteps[4].done = true
    generating.value = false
    generatedQuestions.value = MOCK_AI_GENERATED_QUESTIONS.map(q => ({ ...q, expanded: false }))
    message.success(`成功生成 ${generatedQuestions.value.length} 道题目！`)
  }, 4200)
}

const saveToBank = () => {
  if (typeof window.__addQuestionsToBank === 'function') {
    window.__addQuestionsToBank(generatedQuestions.value)
  } else {
    message.success(`已保存 ${generatedQuestions.value.length} 道题目到题库`)
  }
  generatedQuestions.value = []
  setTimeout(() => {
    import('vue-router').then(({ useRouter }) => {
      // 跳转到题库页查看结果
    })
  }, 500)
}
</script>

<style scoped>
.question-gen-page { padding: 0; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.page-desc { color: #888; font-size: 13px; margin: 4px 0 0; }
.config-card { height: 100%; }
.quick-topics { display: flex; flex-wrap: wrap; gap: 6px; }
.topic-tag { cursor: pointer; font-size: 12px; line-height: 1.4; white-space: normal; }
.type-config { display: flex; flex-direction: column; gap: 12px; }
.type-row { display: flex; align-items: center; }
.type-label { width: 60px; font-size: 13px; color: #555; }
.type-count { width: 30px; text-align: right; font-size: 13px; color: var(--police-primary); font-weight: 600; }
.gen-btn { background: linear-gradient(135deg, #003087, #0050c8); border: none; height: 44px; font-size: 15px; }

/* 空状态 */
.empty-state { display: flex; align-items: center; justify-content: center; min-height: 400px; }
.ai-idle { text-align: center; }
.brain-icon { font-size: 64px; margin-bottom: 16px; }
.idle-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 8px; }
.idle-desc { color: #888; margin-bottom: 24px; }
.feature-list { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; display: inline-flex; }
.feature-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #555; }
.f-icon { font-size: 16px; }

/* 生成中 */
.generating-state { padding: 40px; text-align: center; }
.gen-animation { display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 24px; }
.brain-pulse { font-size: 56px; animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.wave-bars { display: flex; align-items: flex-end; gap: 4px; height: 40px; }
.wave-bar { width: 6px; background: linear-gradient(to top, #003087, #c8a84b); border-radius: 3px; animation: wave 0.8s ease-in-out infinite alternate; }
@keyframes wave { from { height: 8px; } to { height: 36px; } }
.gen-status { font-size: 15px; color: #333; margin-bottom: 16px; }
.gen-steps { display: flex; flex-direction: column; gap: 8px; margin-top: 20px; text-align: left; }
.gen-step { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #aaa; transition: all 0.3s; }
.gen-step.active { color: var(--police-primary); font-weight: 600; }
.gen-step.done { color: #52c41a; }

/* 结果 */
.result-state { }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.result-count { font-size: 15px; font-weight: 600; color: #333; }
.result-actions { display: flex; gap: 8px; }
.question-list { display: flex; flex-direction: column; gap: 12px; max-height: 600px; overflow-y: auto; padding-right: 4px; }
.q-item { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.q-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; cursor: pointer; }
.q-meta { display: flex; align-items: center; gap: 8px; }
.q-num { font-size: 12px; color: #888; }
.q-confidence { display: flex; align-items: center; gap: 8px; }
.conf-label { font-size: 11px; color: #aaa; }
.conf-circle { width: 36px; height: 36px; border-radius: 50%; background: conic-gradient(#003087 calc(var(--conf) * 360deg), #f0f0f0 0); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: #003087; }
.q-content { font-size: 14px; color: #1a1a1a; line-height: 1.6; margin-bottom: 10px; }
.q-options { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.q-option { font-size: 13px; color: #444; padding: 2px 0; }
.opt-label { font-weight: 600; color: var(--police-primary); margin-right: 4px; }
.q-source { font-size: 11px; color: #aaa; }
.q-answer { }
.answer-line { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.ans-label { font-size: 12px; color: #888; }
.ans-value { font-size: 14px; font-weight: 700; color: #52c41a; }
.ans-explain { font-size: 13px; color: #555; line-height: 1.6; margin-bottom: 8px; }
.ai-note { font-size: 12px; color: #888; background: #f8f9ff; padding: 6px 10px; border-radius: 4px; }
.q-toggle { text-align: center; font-size: 12px; color: var(--police-primary); cursor: pointer; margin-top: 8px; }
</style>

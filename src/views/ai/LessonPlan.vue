<template>
  <div class="lesson-plan-page">
    <div class="page-header">
      <div>
        <h2>AI 教案生成</h2>
        <p class="page-desc">输入课题与目标，AI 自动生成完整教案，一键导出 Word</p>
      </div>
      <a-tag color="purple">C2 智能体 · 教案创作</a-tag>
    </div>

    <a-row :gutter="20">
      <!-- 左：输入配置 -->
      <a-col :span="10">
        <a-card title="教案配置" :bordered="false">
          <a-form layout="vertical">
            <a-form-item label="课题名称">
              <a-input v-model:value="config.title" placeholder="如：电信网络诈骗案件侦办实务" />
            </a-form-item>

            <a-form-item label="授课对象">
              <a-radio-group v-model:value="config.audience" button-style="solid">
                <a-radio-button value="basic">基层民警</a-radio-button>
                <a-radio-button value="detective">刑侦警员</a-radio-button>
                <a-radio-button value="leader">基层领导</a-radio-button>
              </a-radio-group>
            </a-form-item>

            <a-form-item label="课时安排">
              <a-select v-model:value="config.duration">
                <a-select-option value="45">45分钟（1课时）</a-select-option>
                <a-select-option value="90">90分钟（2课时）</a-select-option>
                <a-select-option value="180">180分钟（半天）</a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item label="教学目标（每行一个）">
              <a-textarea v-model:value="config.objectives" :rows="4" placeholder="掌握电信诈骗的常见手法&#10;熟悉案件证据固定流程&#10;了解资金追查基本方法" />
            </a-form-item>

            <a-form-item label="参考材料（可选）">
              <a-textarea v-model:value="config.reference" :rows="3" placeholder="粘贴相关法规条文、案例材料等..." />
            </a-form-item>

            <a-form-item label="教学风格">
              <a-radio-group v-model:value="config.style">
                <a-radio value="case">案例导入式</a-radio>
                <a-radio value="lecture">传统讲授式</a-radio>
                <a-radio value="interactive">互动讨论式</a-radio>
              </a-radio-group>
            </a-form-item>

            <a-button
              type="primary" block size="large"
              :loading="generating"
              @click="startGenerate"
              class="gen-btn"
            >
              <template #icon><RobotOutlined /></template>
              {{ generating ? 'AI 生成中...' : '生成教案' }}
            </a-button>
          </a-form>
        </a-card>
      </a-col>

      <!-- 右：教案预览 -->
      <a-col :span="14">
        <!-- 空状态 -->
        <div v-if="!generating && !generatedPlan" class="empty-panel">
          <div class="empty-content">
            <div class="empty-icon">📋</div>
            <p class="empty-title">配置完成后生成教案</p>
            <p class="empty-desc">AI 将根据您的配置生成包含教学目的、重难点、课时分配、教学流程的完整教案</p>
            <div class="sample-structure">
              <div class="ss-title">教案包含以下结构：</div>
              <div v-for="s in planStructure" :key="s" class="ss-item">✓ {{ s }}</div>
            </div>
          </div>
        </div>

        <!-- 生成动画 -->
        <div v-if="generating" class="generating-panel">
          <div class="gen-icon">🤖</div>
          <p class="gen-text">{{ genStatus }}</p>
          <a-progress :percent="genProgress" :stroke-color="{ from: '#003087', to: '#c8a84b' }" status="active" />
        </div>

        <!-- 教案内容 -->
        <div v-if="!generating && generatedPlan" class="plan-preview">
          <div class="plan-toolbar">
            <span class="plan-title-display">{{ generatedPlan.title }}</span>
            <div class="plan-actions">
              <a-button size="small" @click="generatedPlan = null">重新生成</a-button>
              <a-button size="small" type="primary" @click="message.success('教案已导出为Word文档！')">
                <template #icon><DownloadOutlined /></template>导出 Word
              </a-button>
            </div>
          </div>

          <div class="plan-body">
            <div class="plan-meta-grid">
              <div class="pm-item"><span class="pm-l">适用对象</span><span>{{ generatedPlan.audience }}</span></div>
              <div class="pm-item"><span class="pm-l">课时</span><span>{{ generatedPlan.duration }}分钟</span></div>
              <div class="pm-item"><span class="pm-l">教学方式</span><span>{{ generatedPlan.style }}</span></div>
              <div class="pm-item"><span class="pm-l">生成时间</span><span>{{ generatedPlan.genTime }}</span></div>
            </div>

            <div v-for="section in generatedPlan.sections" :key="section.title" class="plan-section">
              <div class="ps-header" @click="section.collapsed = !section.collapsed">
                <span class="ps-num">{{ section.num }}</span>
                <span class="ps-title">{{ section.title }}</span>
                <span class="ps-duration" v-if="section.duration">{{ section.duration }}min</span>
                <span class="ps-toggle">{{ section.collapsed ? '▶' : '▼' }}</span>
              </div>
              <div class="ps-body" v-if="!section.collapsed">
                <div class="ps-content" v-html="section.content.replace(/\n/g, '<br>')"></div>
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
import { RobotOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { MOCK_LESSON_PLAN } from '@/mock/ai-questions'

const generating = ref(false)
const genProgress = ref(0)
const genStatus = ref('')
const generatedPlan = ref(null)

const config = reactive({
  title: '',
  audience: 'basic',
  duration: '90',
  objectives: '',
  reference: '',
  style: 'case',
})

const planStructure = ['课程基本信息', '教学目的与要求', '教学重点与难点', '课时分配表', '教学流程（分节详细步骤）', '板书设计', '作业与思考题']

const startGenerate = () => {
  if (!config.title.trim()) {
    message.warning('请输入课题名称')
    return
  }
  generating.value = true
  genProgress.value = 0

  const steps = [
    { text: '分析课题与教学目标...', prog: 25, delay: 0 },
    { text: '设计教学结构与课时分配...', prog: 55, delay: 1000 },
    { text: '生成各章节详细内容...', prog: 80, delay: 2200 },
    { text: '优化语言与教学建议...', prog: 100, delay: 3400 },
  ]

  steps.forEach(({ text, prog, delay }) => {
    setTimeout(() => {
      genStatus.value = text
      genProgress.value = prog
    }, delay)
  })

const audienceMap = { basic: '基层民警', detective: '刑侦警员', leader: '基层领导' }
const styleMap = { case: '案例导入式', lecture: '传统讲授式', interactive: '互动讨论式' }

  setTimeout(() => {
    generating.value = false
    generatedPlan.value = {
      ...MOCK_LESSON_PLAN,
      title: config.title || MOCK_LESSON_PLAN.title,
      audience: audienceMap[config.audience] || '基层民警',
      duration: config.duration || '90',
      style: styleMap[config.style] || '案例导入式',
      genTime: new Date().toLocaleString('zh-CN'),
      sections: MOCK_LESSON_PLAN.sections.map(s => ({ ...s, collapsed: false })),
    }
    message.success('教案生成完成！')
  }, 4000)
}
</script>

<style scoped>
.lesson-plan-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.page-desc { color: #888; font-size: 13px; margin: 4px 0 0; }
.gen-btn { background: linear-gradient(135deg, #4b0082, #7b2fbe); border: none; height: 44px; font-size: 15px; }
.empty-panel { display: flex; align-items: center; justify-content: center; min-height: 400px; }
.empty-content { text-align: center; }
.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 8px; }
.empty-desc { color: #888; font-size: 13px; margin-bottom: 24px; max-width: 320px; }
.sample-structure { background: #f8f9ff; border-radius: 8px; padding: 16px; text-align: left; display: inline-block; }
.ss-title { font-weight: 600; color: #333; margin-bottom: 8px; }
.ss-item { font-size: 13px; color: #555; margin-bottom: 4px; }
.generating-panel { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; padding: 40px; }
.gen-icon { font-size: 64px; animation: spin 2s linear infinite; }
@keyframes spin { from { transform: rotateY(0deg); } to { transform: rotateY(360deg); } }
.gen-text { font-size: 15px; color: #333; }
.plan-preview { }
.plan-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding: 12px 16px; background: #fff; border-radius: 8px; border: 1px solid #e8e8e8; }
.plan-title-display { font-size: 15px; font-weight: 600; color: var(--police-primary); }
.plan-actions { display: flex; gap: 8px; }
.plan-body { display: flex; flex-direction: column; gap: 8px; max-height: 580px; overflow-y: auto; padding-right: 4px; }
.plan-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #fff; border-radius: 8px; padding: 12px; border: 1px solid #e8e8e8; margin-bottom: 4px; }
.pm-item { display: flex; gap: 8px; font-size: 13px; }
.pm-l { color: #888; min-width: 56px; }
.plan-section { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden; }
.ps-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; cursor: pointer; background: #fafafa; }
.ps-header:hover { background: #f0f5ff; }
.ps-num { width: 24px; height: 24px; border-radius: 50%; background: var(--police-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.ps-title { font-size: 14px; font-weight: 600; color: #1a1a1a; flex: 1; }
.ps-duration { font-size: 12px; color: #888; background: #f0f0f0; padding: 1px 8px; border-radius: 10px; }
.ps-toggle { color: #aaa; font-size: 10px; }
.ps-body { padding: 14px 16px; }
.ps-content { font-size: 13px; color: #555; line-height: 1.8; white-space: pre-line; }
</style>

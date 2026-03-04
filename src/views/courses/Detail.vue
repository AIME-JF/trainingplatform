<template>
  <div class="course-detail-page" :class="{ fullscreen: isFullscreen }">
    <!-- 面包屑 -->
    <a-breadcrumb style="margin-bottom:16px" v-if="!isFullscreen">
      <a-breadcrumb-item @click="$router.push('/courses')" style="cursor:pointer;color:var(--police-primary)">课程中心</a-breadcrumb-item>
      <a-breadcrumb-item>{{ course.title }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-row :gutter="20" v-if="!isFullscreen">
      <!-- 左：内容区 + 课程信息 -->
      <a-col :span="16">
        <!-- 视频课件 -->
        <div v-if="isVideo" class="video-player-wrap">
          <div class="video-player">
            <div class="video-placeholder">
              <div class="play-area" @click="isPlaying = !isPlaying">
                <div class="play-btn" v-if="!isPlaying">▶</div>
                <div class="pause-indicator" v-else>⏸ 播放中</div>
              </div>
              <div class="video-overlay-info">
                <div class="chapter-badge">第 {{ currentChapterIdx+1 }} 章：{{ currentChapter.title }}</div>
              </div>
            </div>
            <!-- 控制栏 -->
            <div class="video-controls">
              <div class="controls-left">
                <button class="ctrl-btn" @click="isPlaying = !isPlaying">{{ isPlaying ? '⏸' : '▶' }}</button>
                <span class="time-display">{{ currentTime }} / {{ currentChapter.duration }}min</span>
              </div>
              <div class="progress-bar-wrap">
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" :style="{ width: playProgress + '%' }"></div>
                </div>
              </div>
              <div class="controls-right">
                <button class="ctrl-btn" @click="isFullscreen = true">⛶ 全屏</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 文档课件 -->
        <div v-else class="doc-viewer-wrap">
          <div class="doc-viewer">
            <div class="doc-header">
              <div class="doc-icon">📄</div>
              <div class="doc-info">
                <div class="doc-title">{{ currentChapter.title || course.title }}</div>
                <div class="doc-meta">
                  <a-tag color="blue">{{ course.fileType === 'document' ? 'PDF / PPT' : '文档' }}</a-tag>
                  <span>{{ currentChapter.duration || 30 }} 分钟阅读</span>
                </div>
              </div>
            </div>
            <div class="doc-content">
              <div class="doc-page" v-for="page in docPages" :key="page.id">
                <div class="page-number">第 {{ page.id }} 页</div>
                <div class="page-title">{{ page.title }}</div>
                <div class="page-text" v-for="(p, i) in page.paragraphs" :key="i">{{ p }}</div>
              </div>
            </div>
            <div class="doc-toolbar">
              <div class="toolbar-left">
                <a-button size="small" @click="docPage > 1 && docPage--" :disabled="docPage <= 1">上一页</a-button>
                <span class="page-indicator">{{ docPage }} / {{ docTotalPages }}</span>
                <a-button size="small" @click="docPage < docTotalPages && docPage++" :disabled="docPage >= docTotalPages">下一页</a-button>
              </div>
              <div class="toolbar-right">
                <a-button size="small" @click="docZoom = Math.max(80, docZoom - 10)">A-</a-button>
                <span class="zoom-indicator">{{ docZoom }}%</span>
                <a-button size="small" @click="docZoom = Math.min(150, docZoom + 10)">A+</a-button>
                <a-button size="small" type="primary" ghost @click="message.success('文档已下载')">
                  <template #icon><DownloadOutlined /></template>下载
                </a-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 课程信息 Tabs -->
        <a-card :bordered="false" style="margin-top:16px">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="intro" tab="课程简介">
              <p style="line-height:1.8;color:#444">{{ course.description }}</p>
              <div class="meta-grid">
                <div class="meta-item"><span class="meta-l">主讲教官</span><span>{{ course.instructor }}</span></div>
                <div class="meta-item"><span class="meta-l">课程时长</span><span>{{ course.duration }} 分钟</span></div>
                <div class="meta-item"><span class="meta-l">课件类型</span><span>{{ isVideo ? '🎬 视频课程' : '📄 文档课程' }}</span></div>
                <div class="meta-item"><span class="meta-l">学员人数</span><span>{{ course.studentCount.toLocaleString() }} 人</span></div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="notes" tab="笔记">
              <a-textarea placeholder="记录学习笔记..." :rows="5" />
              <a-button type="primary" style="margin-top:8px" @click="notesSaved = true; setTimeout(() => notesSaved = false, 2000)">{{ notesSaved ? '✓ 已保存' : '保存笔记' }}</a-button>
            </a-tab-pane>
            <a-tab-pane key="qa" tab="答疑区">
              <div class="qa-list">
                <div class="qa-item" v-for="q in mockQA" :key="q.id">
                  <div class="qa-question">
                    <a-avatar size="small" style="background:#003087">{{ q.user.charAt(0) }}</a-avatar>
                    <span class="qa-user">{{ q.user }}</span>
                    <span class="qa-text">{{ q.question }}</span>
                  </div>
                  <div class="qa-answer" v-if="q.answer">
                    <a-tag color="gold" size="small">教官回复</a-tag>
                    {{ q.answer }}
                  </div>
                </div>
              </div>
              <a-input-search placeholder="提问..." enter-button="提交" style="margin-top:12px" />
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>

      <!-- 右：章节列表 -->
      <a-col :span="8">
        <a-card :title="isVideo ? '课程章节' : '文档目录'" :bordered="false">
          <div class="chapter-list">
            <div
              v-for="(ch, idx) in course.chapters"
              :key="idx"
              class="chapter-item"
              :class="{ active: currentChapterIdx === idx, locked: ch.locked }"
              @click="selectChapter(idx, ch)"
            >
              <div class="ch-left">
                <div class="ch-num">{{ idx+1 }}</div>
                <div class="ch-info">
                  <div class="ch-title">{{ ch.title }}</div>
                  <div class="ch-meta">{{ ch.duration }}分钟 · {{ isVideo ? '视频' : '阅读' }}</div>
                </div>
              </div>
              <div class="ch-right">
                <a-progress v-if="!ch.locked && ch.progress > 0" type="circle" :percent="ch.progress" :width="32" />
                <LockOutlined v-if="ch.locked" style="color:#bbb" />
                <CheckCircleFilled v-if="ch.progress === 100" style="color:#52c41a;font-size:18px" />
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 全屏模式（仅视频） -->
    <div v-if="isFullscreen && isVideo" class="fullscreen-player">
      <div class="fs-video">
        <div class="play-area-fs" @click="isPlaying = !isPlaying">
          <div class="fs-chapter-title">{{ currentChapter.title }}</div>
          <div class="play-btn-fs" v-if="!isPlaying">▶</div>
        </div>
      </div>
      <button class="exit-fullscreen" @click="isFullscreen = false">✕ 退出全屏</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { LockOutlined, CheckCircleFilled, DownloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { MOCK_COURSES } from '@/mock/courses'

const route = useRoute()
const courseId = route.params.id
const course = computed(() => MOCK_COURSES.find(c => c.id === courseId) || MOCK_COURSES[0])

const isVideo = computed(() => (course.value.fileType || 'video') === 'video')

const currentChapterIdx = ref(0)
const currentChapter = computed(() => course.value.chapters[currentChapterIdx.value] || {})
const isPlaying = ref(false)
const isFullscreen = ref(false)
const activeTab = ref('intro')
const playProgress = ref(35)
const currentTime = ref('12:30')
const notesSaved = ref(false)
const docPage = ref(1)
const docTotalPages = ref(12)
const docZoom = ref(100)

const selectChapter = (idx, ch) => {
  if (ch.locked) return
  currentChapterIdx.value = idx
  isPlaying.value = false
  playProgress.value = ch.progress || 0
  docPage.value = 1
}

// 文档模拟内容
const docPages = computed(() => {
  const ch = currentChapter.value
  return [
    {
      id: 1,
      title: ch.title || '概述',
      paragraphs: [
        '本章节重点介绍相关法律条文的实际应用场景，结合广西地区公安执法实际情况进行深入分析。',
        '学习目标：掌握相关法规的核心要点，能够在执法实践中正确运用，提升规范化执法能力。',
        '本章内容共分为三个部分：基础概念、案例分析和操作规范。',
      ]
    },
    {
      id: 2,
      title: '核心知识点',
      paragraphs: [
        '一、法律依据与适用范围：根据《中华人民共和国刑事诉讼法》第一百一十五条规定……',
        '二、执法程序与规范要求：在进行相关执法活动时，应当严格遵循法定程序，确保当事人合法权益。',
        '三、证据收集与固定：要注重证据链的完整性，确保每一环节都有据可查。',
      ]
    },
    {
      id: 3,
      title: '案例分析',
      paragraphs: [
        '【案例一】2024年3月，南宁市某派出所在处理一起邻里纠纷时……',
        '【分析要点】本案中涉及的关键法律问题包括：管辖权确认、调解程序规范、当事人权益保障。',
        '【案例二】桂林市某物业管理纠纷中的执法规范化问题……',
      ]
    },
  ]
})

const mockQA = [
  { id: 1, user: '张民警', question: '第3章的拘留时限是指连续72小时还是可以延长？', answer: '拘留后侦查羁押一般不超过37天，但有特殊情形可申请延长。' },
  { id: 2, user: '李警员', question: '视频中的表格能下载吗？', answer: null },
]
</script>

<style scoped>
.course-detail-page { padding: 0; }

/* 视频播放器样式 */
.video-player-wrap { background: #000; border-radius: 8px; overflow: hidden; }
.video-player { position: relative; }
.video-placeholder { background: linear-gradient(135deg, #001236, #003087); height: 380px; display: flex; align-items: center; justify-content: center; position: relative; cursor: pointer; }
.play-area { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; height: 100%; }
.play-btn { width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 32px; color: #fff; backdrop-filter: blur(4px); }
.pause-indicator { font-size: 20px; color: rgba(255,255,255,0.8); }
.video-overlay-info { position: absolute; bottom: 60px; left: 16px; }
.chapter-badge { background: rgba(0,0,0,0.6); color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 13px; }
.video-controls { background: #111; padding: 8px 16px; display: flex; align-items: center; gap: 12px; }
.controls-left { display: flex; align-items: center; gap: 8px; }
.ctrl-btn { background: transparent; border: none; color: #fff; font-size: 18px; cursor: pointer; padding: 4px 8px; }
.time-display { color: #aaa; font-size: 12px; white-space: nowrap; }
.progress-bar-wrap { flex: 1; }
.progress-bar-bg { height: 4px; background: #333; border-radius: 2px; cursor: pointer; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, #003087, #c8a84b); border-radius: 2px; transition: width 0.3s; }
.controls-right { white-space: nowrap; }

/* 文档阅读器样式 */
.doc-viewer-wrap { border-radius: 8px; overflow: hidden; border: 1px solid #e8e8e8; }
.doc-viewer { background: #fff; }
.doc-header { display: flex; align-items: center; gap: 16px; padding: 20px 24px; background: linear-gradient(135deg, #f0f5ff, #e8f0fe); border-bottom: 1px solid #d0e0ff; }
.doc-icon { font-size: 48px; }
.doc-title { font-size: 18px; font-weight: 600; color: #001234; margin-bottom: 4px; }
.doc-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
.doc-content { padding: 24px 32px; max-height: 320px; overflow-y: auto; background: #fafbfc; }
.doc-page { margin-bottom: 20px; }
.page-number { font-size: 11px; color: #aaa; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
.page-title { font-size: 16px; font-weight: 600; color: #1a1a1a; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid var(--police-primary, #003087); display: inline-block; }
.page-text { font-size: 14px; line-height: 1.9; color: #444; margin-bottom: 8px; text-indent: 2em; }
.doc-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; background: #f5f5f5; border-top: 1px solid #e8e8e8; }
.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; }
.page-indicator { font-size: 13px; color: #555; min-width: 60px; text-align: center; }
.zoom-indicator { font-size: 12px; color: #888; min-width: 40px; text-align: center; }

/* 通用样式 */
.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
.meta-item { display: flex; gap: 8px; font-size: 13px; }
.meta-l { color: #888; min-width: 60px; }
.chapter-list { display: flex; flex-direction: column; gap: 8px; max-height: 500px; overflow-y: auto; }
.chapter-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.chapter-item:hover:not(.locked) { background: #f0f5ff; border-color: #d0e0ff; }
.chapter-item.active { background: #e8f0fe; border-color: var(--police-primary); }
.chapter-item.locked { opacity: 0.5; cursor: not-allowed; }
.ch-left { display: flex; align-items: center; gap: 10px; flex: 1; }
.ch-num { width: 24px; height: 24px; border-radius: 50%; background: var(--police-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; }
.chapter-item.active .ch-num { background: var(--police-gold); }
.ch-title { font-size: 13px; font-weight: 500; color: #333; }
.ch-meta { font-size: 11px; color: #888; }
.qa-list { display: flex; flex-direction: column; gap: 12px; }
.qa-item { border-left: 3px solid var(--police-primary); padding-left: 12px; }
.qa-question { display: flex; align-items: center; gap: 8px; }
.qa-user { font-size: 12px; color: #888; }
.qa-text { font-size: 13px; color: #333; }
.qa-answer { margin-top: 6px; font-size: 13px; color: #555; background: #fffbe6; padding: 6px 10px; border-radius: 4px; }
.fullscreen-player { position: fixed; inset: 0; background: #000; z-index: 1000; display: flex; align-items: center; justify-content: center; }
.fs-video { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #000820, #001a50); }
.play-area-fs { display: flex; flex-direction: column; align-items: center; gap: 24px; cursor: pointer; }
.fs-chapter-title { color: rgba(255,255,255,0.7); font-size: 18px; }
.play-btn-fs { width: 96px; height: 96px; border-radius: 50%; background: rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center; font-size: 48px; color: #fff; }
.exit-fullscreen { position: absolute; top: 24px; right: 24px; background: rgba(255,255,255,0.15); border: none; color: #fff; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }
</style>

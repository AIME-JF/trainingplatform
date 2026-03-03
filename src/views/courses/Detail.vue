<template>
  <div class="course-detail-page" :class="{ fullscreen: isFullscreen }">
    <!-- 面包屑 -->
    <a-breadcrumb style="margin-bottom:16px" v-if="!isFullscreen">
      <a-breadcrumb-item @click="$router.push('/courses')" style="cursor:pointer;color:var(--police-primary)">课程中心</a-breadcrumb-item>
      <a-breadcrumb-item>{{ course.title }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-row :gutter="20" v-if="!isFullscreen">
      <!-- 左：视频区 + 课程信息 -->
      <a-col :span="16">
        <!-- 视频播放器 -->
        <div class="video-player-wrap">
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

        <!-- 课程信息 Tabs -->
        <a-card :bordered="false" style="margin-top:16px">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="intro" tab="课程简介">
              <p style="line-height:1.8;color:#444">{{ course.description }}</p>
              <div class="meta-grid">
                <div class="meta-item"><span class="meta-l">主讲教官</span><span>{{ course.instructor }}</span></div>
                <div class="meta-item"><span class="meta-l">课程时长</span><span>{{ course.duration }} 分钟</span></div>
                <div class="meta-item"><span class="meta-l">章节数量</span><span>{{ course.chapters.length }} 章</span></div>
                <div class="meta-item"><span class="meta-l">学员人数</span><span>{{ course.studentCount.toLocaleString() }} 人</span></div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="notes" tab="笔记">
              <a-textarea placeholder="记录学习笔记..." :rows="5" />
              <a-button type="primary" style="margin-top:8px">保存笔记</a-button>
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
        <a-card title="课程章节" :bordered="false">
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
                  <div class="ch-meta">{{ ch.duration }}分钟</div>
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

    <!-- 全屏模式 -->
    <div v-if="isFullscreen" class="fullscreen-player">
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
import { LockOutlined, CheckCircleFilled } from '@ant-design/icons-vue'
import { MOCK_COURSES } from '@/mock/courses'

const route = useRoute()
const courseId = route.params.id
const course = computed(() => MOCK_COURSES.find(c => c.id === courseId) || MOCK_COURSES[0])

const currentChapterIdx = ref(0)
const currentChapter = computed(() => course.value.chapters[currentChapterIdx.value] || {})
const isPlaying = ref(false)
const isFullscreen = ref(false)
const activeTab = ref('intro')
const playProgress = ref(35)
const currentTime = ref('12:30')

const selectChapter = (idx, ch) => {
  if (ch.locked) return
  currentChapterIdx.value = idx
  isPlaying.value = false
  playProgress.value = ch.progress || 0
}

const mockQA = [
  { id: 1, user: '张民警', question: '第3章的拘留时限是指连续72小时还是可以延长？', answer: '拘留后侦查羁押一般不超过37天，但有特殊情形可申请延长。' },
  { id: 2, user: '李警员', question: '视频中的表格能下载吗？', answer: null },
]
</script>

<style scoped>
.course-detail-page { padding: 0; }
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

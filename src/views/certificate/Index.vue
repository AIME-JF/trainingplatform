<template>
  <div class="cert-page">
    <!-- 页头 -->
    <div class="page-header-bar">
      <div>
        <h2 class="page-h2">结业证书</h2>
        <p class="page-sub">我的训练结业证书</p>
      </div>
      <a-button v-if="isAdmin" type="primary" @click="issueVisible = true"><PlusOutlined /> 颁发证书</a-button>
    </div>

    <!-- 学员证书列表 -->
    <div class="cert-grid">
      <div class="cert-card" v-for="cert in certificates" :key="cert.id">
        <!-- 证书主体 -->
        <div class="cert-body" :id="`cert-${cert.id}`">
          <div class="cert-watermark">警</div>
          <div class="cert-top">
            <div class="cert-emblem">警</div>
            <div class="cert-org">广西壮族自治区公安厅</div>
          </div>
          <div class="cert-main-title">警务训练结业证书</div>
          <div class="cert-content">
            <p>兹证明 <span class="cert-name">{{ cert.studentName }}</span> 同志</p>
            <p>于 <span class="cert-highlight">{{ cert.startDate }}</span> 至 <span class="cert-highlight">{{ cert.endDate }}</span></p>
            <p>参加 <span class="cert-course">{{ cert.trainingName }}</span></p>
            <p>考核成绩 <span class="cert-score">{{ cert.score }} 分</span>，成绩合格，准予结业。</p>
          </div>
          <div class="cert-footer">
            <div class="cert-no">证书编号：{{ cert.certNo }}</div>
            <div class="cert-date">颁发日期：{{ cert.issueDate }}</div>
            <div class="cert-seal">（印）</div>
          </div>
        </div>
        <!-- 操作栏 -->
        <div class="cert-actions">
          <a-button block @click="downloadCert(cert)"><DownloadOutlined /> 下载证书</a-button>
          <a-space style="margin-top:8px">
            <a-tag color="green">有效</a-tag>
            <span class="cert-valid">有效期至 {{ cert.expireDate }}</span>
          </a-space>
        </div>
      </div>

      <!-- 空态 -->
      <div class="cert-empty" v-if="certificates.length === 0">
        <a-empty description="暂无结业证书">
          <a-button type="primary" @click="$router.push('/courses')">去学习课程</a-button>
        </a-empty>
      </div>
    </div>

    <!-- 颁发证书 Modal（管理员用） -->
    <a-modal v-model:open="issueVisible" title="颁发结业证书" @ok="handleIssue" ok-text="确认颁发" :confirm-loading="issuing">
      <a-form :model="issueForm" layout="vertical">
        <a-form-item label="选择学员">
          <a-select v-model:value="issueForm.studentId" placeholder="请选择学员" show-search :filter-option="filterStudent">
            <a-select-option v-for="u in studentOptions" :key="u.id" :value="u.id">
              {{ u.name }} · {{ u.policeId }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="培训班">
          <a-select v-model:value="issueForm.trainingId" placeholder="请选择培训班">
            <a-select-option v-for="t in endedTrainings" :key="t.id" :value="t.id">
              {{ t.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="考核成绩">
              <a-input-number v-model:value="issueForm.score" :min="0" :max="100" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="颁发日期">
              <a-date-picker v-model:value="issueForm.issueDate" style="width:100%" value-format="YYYY-MM-DD" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth.js'
import { MOCK_TRAININGS } from '../../mock/trainings.js'
import { MOCK_USER_LIST } from '../../mock/users.js'

const authStore = useAuthStore()
const isAdmin = authStore.isAdmin

const certificates = ref([
  {
    id: 'cert001',
    certNo: 'GXGA-2025-0312-0089',
    studentName: '张伟',
    trainingName: '2024年南宁市基层民警执法规范化培训（第2期）',
    startDate: '2024-11-06',
    endDate: '2024-11-17',
    score: 89,
    issueDate: '2024-11-22',
    expireDate: '2026-11-22',
  },
  {
    id: 'cert002',
    certNo: 'GXGA-2024-0816-0156',
    studentName: '张伟',
    trainingName: '2024年广西公安刑事侦查专项培训（第1期）',
    startDate: '2024-08-05',
    endDate: '2024-08-16',
    score: 92,
    issueDate: '2024-08-20',
    expireDate: '2026-08-20',
  },
])

// 动态下拉数据
const studentOptions = MOCK_USER_LIST.filter(u => u.status === 'active')
const endedTrainings = MOCK_TRAININGS.filter(t => t.status === 'ended' || t.status === 'active')
function filterStudent(input, option) {
  const u = studentOptions.find(s => s.id === option.value)
  return u && (u.name.includes(input) || u.policeId.toLowerCase().includes(input.toLowerCase()))
}

const issueVisible = ref(false)
const issuing = ref(false)
const issueForm = ref({ studentId: '', trainingId: '', score: 80, issueDate: '' })

function downloadCert(cert) {
  const style = document.createElement('style')
  style.innerHTML = `
    @media print {
      body * { visibility: hidden !important; }
      #cert-${cert.id}, #cert-${cert.id} * { visibility: visible !important; }
      #cert-${cert.id} { position: fixed; top: 0; left: 0; width: 100%; }
    }
  `
  document.head.appendChild(style)
  window.print()
  setTimeout(() => document.head.removeChild(style), 1000)
}

async function handleIssue() {
  if (!issueForm.value.studentId || !issueForm.value.trainingId) {
    message.warning('请填写完整信息')
    return
  }
  issuing.value = true
  await new Promise(r => setTimeout(r, 800))
  const now = new Date()
  const student = MOCK_USER_LIST.find(u => u.id === issueForm.value.studentId)
  const training = MOCK_TRAININGS.find(t => t.id === issueForm.value.trainingId)
  certificates.value.unshift({
    id: `cert${Date.now()}`,
    certNo: `GXGA-${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}-${String(Math.floor(Math.random()*900)+100)}`,
    studentName: student?.name || '未知',
    trainingName: training?.name || '未知培训班',
    startDate: training?.startDate || '',
    endDate: training?.endDate || '',
    score: issueForm.value.score,
    issueDate: issueForm.value.issueDate || now.toISOString().split('T')[0],
    expireDate: `${now.getFullYear()+2}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`,
  })
  issuing.value = false
  issueVisible.value = false
  message.success('证书已成功颁发')
  issueForm.value = { studentId: '', trainingId: '', score: 80, issueDate: '' }
}
</script>

<style scoped>
.cert-page { }
.page-header-bar { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-h2 { font-size: 20px; font-weight: 700; color: #001234; margin: 0 0 4px; }
.page-sub { font-size: 13px; color: #8c8c8c; margin: 0; }

.cert-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }

.cert-card { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1); border: 1px solid #e8e8e8; }

/* 证书主体 */
.cert-body {
  background: linear-gradient(135deg, #001234 0%, #003087 100%);
  padding: 32px 28px;
  position: relative;
  overflow: hidden;
  min-height: 280px;
}

.cert-watermark {
  position: absolute;
  font-size: 180px;
  font-weight: 900;
  color: rgba(255,255,255,0.04);
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  user-select: none;
}

.cert-top { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.cert-emblem {
  width: 40px; height: 40px; background: #c8a84b; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 900; color: #001234;
}
.cert-org { color: rgba(255,255,255,0.8); font-size: 13px; letter-spacing: 1px; }

.cert-main-title {
  font-size: 22px; font-weight: 900; color: #c8a84b;
  letter-spacing: 4px; text-align: center; margin-bottom: 20px;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.cert-content { color: rgba(255,255,255,0.9); line-height: 2; font-size: 14px; }
.cert-content p { margin: 0; }
.cert-name { font-size: 18px; font-weight: 700; color: white; border-bottom: 1px solid rgba(200,168,75,0.6); padding: 0 4px; }
.cert-highlight { color: #c8a84b; font-weight: 600; }
.cert-course { color: white; font-weight: 600; }
.cert-score { font-size: 18px; font-weight: 700; color: #52c41a; }

.cert-footer {
  margin-top: 20px; display: flex; justify-content: space-between; align-items: flex-end;
  padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.15);
}
.cert-no, .cert-date { font-size: 11px; color: rgba(255,255,255,0.5); font-family: monospace; }
.cert-seal { font-size: 24px; color: rgba(200,168,75,0.4); font-weight: 900; }

/* 操作栏 */
.cert-actions { padding: 16px; display: flex; flex-direction: column; }
.cert-valid { font-size: 12px; color: #8c8c8c; }

.cert-empty { grid-column: 1 / -1; padding: 60px; }

@media (max-width: 768px) {
  .cert-grid { grid-template-columns: 1fr; }
}
</style>

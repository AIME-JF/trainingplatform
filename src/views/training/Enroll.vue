<template>
  <div class="enroll-page">
    <!-- 培训班信息头部 -->
    <div class="training-header">
      <div class="header-badge">
        <a-tag color="green">报名中</a-tag>
      </div>
      <h2 class="training-title">2025年南宁市基层民警执法规范化培训（第3期）</h2>
      <div class="training-meta-row">
        <span><CalendarOutlined /> 2025-03-10 至 2025-03-21（12天）</span>
        <span><EnvironmentOutlined /> 南宁市公安局培训基地</span>
        <span><UserOutlined /> 主讲教官：李志强</span>
      </div>
      <!-- 名额进度 -->
      <div class="quota-section">
        <div class="quota-label">
          <span>名额情况</span>
          <span class="quota-nums"><b>32</b> / 50 人已录取</span>
        </div>
        <a-progress :percent="64" :show-info="false" stroke-color="#003087" />
        <div class="quota-tags">
          <a-tag color="green">已录取 32</a-tag>
          <a-tag color="orange">待审核 8</a-tag>
          <a-tag color="default">剩余名额 10</a-tag>
        </div>
      </div>
    </div>

    <!-- 已提交状态 -->
    <div v-if="submitted" class="submit-success">
      <a-result
        status="success"
        title="报名申请已提交！"
        sub-title="您的报名申请正在审核中，审核结果将通过系统消息通知您，请耐心等待。"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/training')">返回培训列表</a-button>
          <a-button @click="$router.push('/')">回到首页</a-button>
        </template>
      </a-result>
    </div>

    <!-- 报名表单 -->
    <div v-else class="enroll-form-card">
      <h3 class="form-title">填写报名信息</h3>
      <a-form :model="formData" layout="vertical" :label-col="{ span: 24 }">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12">
            <a-form-item label="姓名">
              <a-input v-model:value="formData.name" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="警号">
              <a-input v-model:value="formData.policeId" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="所属单位">
              <a-input v-model:value="formData.unit" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="联系电话">
              <a-input v-model:value="formData.phone" placeholder="请输入联系电话" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="参训目的（选填）">
              <a-textarea v-model:value="formData.reason" :rows="3" placeholder="请简要说明参训原因或目标..." :maxlength="200" show-count />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="是否有住宿需求">
              <a-radio-group v-model:value="formData.needAccom">
                <a-radio value="yes">需要住宿</a-radio>
                <a-radio value="no">不需要（自行解决）</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>

        <div class="form-agreement">
          <a-checkbox v-model:checked="agreed">
            我已阅读并同意<a>《培训班报名须知》</a>，确认参训期间遵守培训纪律
          </a-checkbox>
        </div>

        <div class="form-actions">
          <a-button @click="$router.back()">返回</a-button>
          <a-button type="primary" :loading="submitting" :disabled="!agreed" @click="handleSubmit">
            提交报名申请
          </a-button>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined } from '@ant-design/icons-vue'

const submitted = ref(false)
const submitting = ref(false)
const agreed = ref(false)

const formData = ref({
  name: '张伟',
  policeId: 'GX-NN-2056',
  unit: '南宁市青秀区公安局刑警大队',
  phone: '136****0003',
  reason: '',
  needAccom: 'no',
})

async function handleSubmit() {
  if (!agreed.value) { message.warning('请先同意报名须知'); return }
  submitting.value = true
  await new Promise(r => setTimeout(r, 1000))
  submitting.value = false
  submitted.value = true
  message.success('报名申请已提交，等待审核')
}
</script>

<style scoped>
.enroll-page { max-width: 760px; margin: 0 auto; }
.training-header {
  background: white;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.header-badge { margin-bottom: 10px; }
.training-title { font-size: 18px; font-weight: 700; color: #001234; margin-bottom: 12px; }
.training-meta-row {
  display: flex; flex-wrap: wrap; gap: 16px;
  font-size: 13px; color: #595959; margin-bottom: 16px;
}
.quota-section { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.quota-label { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; color: #595959; }
.quota-nums b { color: #003087; font-size: 16px; }
.quota-tags { display: flex; gap: 8px; margin-top: 8px; }
.enroll-form-card {
  background: white; border-radius: 10px; padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.form-title { font-size: 16px; font-weight: 700; margin-bottom: 20px; color: #001234; }
.form-agreement { margin-bottom: 20px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.submit-success { background: white; border-radius: 10px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
</style>

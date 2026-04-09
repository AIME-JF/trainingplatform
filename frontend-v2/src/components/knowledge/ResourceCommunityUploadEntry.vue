<template>
  <a-button class="community-upload-btn" @click="handleClick">
    <template #icon>
      <UploadOutlined />
    </template>
    上传
  </a-button>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { UploadOutlined } from '@ant-design/icons-vue'

const router = useRouter()

function handleClick() {
  void router.push('/resource/my')
}
</script>

<style scoped>
.community-upload-btn {
  min-width: 92px !important;
  height: 44px !important;
  padding: 0 18px !important;
  border: none !important;
  border-radius: 16px !important;
  background: rgba(255, 255, 255, 0.94) !important;
  color: #111827 !important;
  box-shadow: 0 14px 28px rgba(255, 255, 255, 0.16) !important;
  font-size: 18px !important;
  font-weight: 700 !important;
}

.community-upload-btn:hover:not(:disabled),
.community-upload-btn:focus:not(:disabled) {
  background: #fff !important;
  color: #111827 !important;
  transform: translateY(-1px);
}

.community-upload-btn:disabled {
  opacity: 0.6;
}

.community-upload-btn :deep(.anticon) {
  font-size: 16px;
}

@media (max-width: 768px) {
  .community-upload-btn {
    min-width: 84px !important;
    height: 42px !important;
    padding: 0 16px !important;
    font-size: 17px !important;
  }
}
</style>

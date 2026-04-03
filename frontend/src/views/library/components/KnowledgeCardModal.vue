<template>
  <a-modal
    :open="open"
    :title="itemId ? '编辑知识点' : '新建知识点'"
    :width="860"
    :footer="null"
    :destroy-on-close="true"
    @cancel="handleClose"
  >
    <a-form layout="vertical">
      <a-form-item label="标题" required>
        <a-input v-model:value="title" :maxlength="200" placeholder="输入知识点标题" />
      </a-form-item>
      <a-form-item label="目标文件夹">
        <a-select v-model:value="targetFolderId" allow-clear placeholder="默认保存到根目录">
          <a-select-option :value="null">根目录</a-select-option>
          <a-select-option
            v-for="folder in folderOptions"
            :key="folder.value"
            :value="folder.value"
          >
            {{ folder.label }}
          </a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="知识点内容" required>
        <div class="editor-shell">
          <div class="editor-toolbar">
            <a-button size="small" @click="execCommand('bold')">加粗</a-button>
            <a-button size="small" @click="execCommand('italic')">斜体</a-button>
            <a-button size="small" @click="execCommand('insertUnorderedList')">列表</a-button>
            <a-button size="small" @click="execCommand('formatBlock', 'h2')">标题</a-button>
            <a-button size="small" @click="execCommand('removeFormat')">清除格式</a-button>
          </div>
          <div
            ref="editorRef"
            class="editor-content"
            contenteditable="true"
            @input="handleEditorInput"
          />
        </div>
      </a-form-item>
    </a-form>

    <div class="modal-footer">
      <a-button @click="handleClose">取消</a-button>
      <a-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ submitting ? '保存中' : (itemId ? '保存修改' : '创建知识点') }}
      </a-button>
    </div>
  </a-modal>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { createLibraryKnowledgeItem, updateLibraryItem } from '@/api/library'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  folderOptions: {
    type: Array,
    default: () => [],
  },
  defaultFolderId: {
    type: [Number, null],
    default: null,
  },
  itemId: {
    type: [Number, null],
    default: null,
  },
  initialTitle: {
    type: String,
    default: '',
  },
  initialContent: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:open', 'success'])

const editorRef = ref(null)
const title = ref('')
const targetFolderId = ref(null)
const contentHtml = ref('')
const submitting = ref(false)

watch(
  () => props.open,
  async (visible) => {
    if (!visible) {
      return
    }
    title.value = props.initialTitle || ''
    contentHtml.value = props.initialContent || ''
    targetFolderId.value = props.defaultFolderId ?? null
    await nextTick()
    if (editorRef.value) {
      editorRef.value.innerHTML = contentHtml.value || '<p><br></p>'
    }
  },
  { immediate: true },
)

function execCommand(command, value = null) {
  editorRef.value?.focus()
  document.execCommand(command, false, value)
  handleEditorInput()
}

function handleEditorInput() {
  contentHtml.value = editorRef.value?.innerHTML || ''
}

async function handleSubmit() {
  if (!title.value.trim()) {
    message.warning('请输入知识点标题')
    return
  }
  if (!String(contentHtml.value || '').replace(/<[^>]+>/g, '').trim()) {
    message.warning('请输入知识点内容')
    return
  }

  submitting.value = true
  try {
    if (props.itemId) {
      await updateLibraryItem(props.itemId, {
        title: title.value.trim(),
        knowledgeContentHtml: contentHtml.value,
      })
      message.success('知识点已更新')
    } else {
      await createLibraryKnowledgeItem({
        title: title.value.trim(),
        folderId: targetFolderId.value,
        knowledgeContentHtml: contentHtml.value,
      })
      message.success('知识点已创建')
    }
    emit('success')
    emit('update:open', false)
  } catch (error) {
    message.error(error?.message || '知识点保存失败')
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  if (submitting.value) {
    return
  }
  emit('update:open', false)
}
</script>

<style scoped>
.editor-shell {
  border: 1px solid #d8e0ec;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid #edf2f7;
  background: #f8fbff;
}

.editor-content {
  min-height: 260px;
  padding: 16px 18px;
  line-height: 1.8;
  outline: none;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>

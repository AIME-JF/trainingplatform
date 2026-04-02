import { ref, watch, type Ref } from 'vue'
import { message } from 'ant-design-vue'
import type {
  ResourceCommentResponse,
  ResourceDetailResponse,
} from '@/api/learning-resource'
import {
  createResourceComment,
  deleteResourceComment,
  likeResource,
  listResourceComments,
  shareResource,
  unlikeResource,
} from '@/api/learning-resource'

interface UseResourceInteractionsOptions {
  resource: Ref<ResourceDetailResponse | null>
  isMobile: Ref<boolean>
  patchResource: (resourceId: number, patch: Partial<ResourceDetailResponse>) => void
}

export function useResourceInteractions(options: UseResourceInteractionsOptions) {
  const { resource, isMobile, patchResource } = options

  const liking = ref(false)
  const sharing = ref(false)
  const commentDrawerOpen = ref(false)
  const commentLoading = ref(false)
  const commentSubmitting = ref(false)
  const comments = ref<ResourceCommentResponse[]>([])
  const commentDraft = ref('')

  watch(commentDrawerOpen, async (open) => {
    if (!open) {
      commentDraft.value = ''
      return
    }

    if (resource.value?.id) {
      await loadComments(resource.value.id)
    }
  })

  watch(() => resource.value?.id, async (resourceId, previousResourceId) => {
    if (!commentDrawerOpen.value || !resourceId || resourceId === previousResourceId) {
      return
    }
    await loadComments(resourceId)
  })

  async function handleToggleLike() {
    if (!resource.value?.id || liking.value) {
      return
    }

    liking.value = true
    try {
      const current = resource.value
      if (!current?.id) {
        return
      }

      const response = current.current_user_liked
        ? await unlikeResource(current.id)
        : await likeResource(current.id)

      patchResource(current.id, {
        current_user_liked: response.liked,
        like_count: response.like_count,
      })
    } catch (error) {
      message.error(error instanceof Error ? error.message : '点赞操作失败')
    } finally {
      liking.value = false
    }
  }

  async function handleShare() {
    if (!resource.value?.id || sharing.value) {
      return
    }

    sharing.value = true
    try {
      const resourceId = resource.value.id
      const response = await shareResource(resourceId)
      patchResource(resourceId, { share_count: response.share_count })

      const copied = await copyShareLink(resourceId)
      message.success(copied ? '已复制链接并记录转发' : '已记录转发')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '转发失败')
    } finally {
      sharing.value = false
    }
  }

  async function copyShareLink(resourceId: number) {
    const shareUrl = new URL(`/resource/detail/${resourceId}`, window.location.origin).toString()

    if (isMobile.value && typeof navigator !== 'undefined' && 'share' in navigator) {
      try {
        await navigator.share({
          title: resource.value?.title,
          text: resource.value?.summary || resource.value?.title,
          url: shareUrl,
        })
        return true
      } catch {
        // fallback to clipboard
      }
    }

    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(shareUrl)
      return true
    }

    const textarea = document.createElement('textarea')
    textarea.value = shareUrl
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    const copied = document.execCommand('copy')
    document.body.removeChild(textarea)
    return copied
  }

  function openComments() {
    if (!resource.value?.id) {
      return
    }
    commentDrawerOpen.value = true
  }

  async function loadComments(resourceId: number) {
    commentLoading.value = true
    try {
      comments.value = await listResourceComments(resourceId)
      patchResource(resourceId, { comment_count: comments.value.length })
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载评论失败')
    } finally {
      commentLoading.value = false
    }
  }

  async function handleSubmitComment() {
    if (!resource.value?.id || commentSubmitting.value) {
      return
    }

    const content = commentDraft.value.trim()
    if (!content) {
      message.warning('请输入评论内容')
      return
    }

    commentSubmitting.value = true
    try {
      const created = await createResourceComment(resource.value.id, { content })
      comments.value = [created, ...comments.value]
      commentDraft.value = ''
      patchResource(resource.value.id, { comment_count: comments.value.length })
      message.success('评论已发布')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '发表评论失败')
    } finally {
      commentSubmitting.value = false
    }
  }

  async function handleDeleteComment(commentId: number) {
    if (!resource.value?.id) {
      return
    }

    try {
      await deleteResourceComment(resource.value.id, commentId)
      comments.value = comments.value.filter((item) => item.id !== commentId)
      patchResource(resource.value.id, { comment_count: comments.value.length })
      message.success('评论已删除')
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除评论失败')
    }
  }

  return {
    liking,
    sharing,
    commentDrawerOpen,
    commentLoading,
    commentSubmitting,
    comments,
    commentDraft,
    handleToggleLike,
    handleShare,
    openComments,
    handleSubmitComment,
    handleDeleteComment,
  }
}

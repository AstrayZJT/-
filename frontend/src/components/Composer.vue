<script setup>
import { ref } from 'vue'
import { api } from '../api'
import { store, notify } from '../store'
import Avatar from './Avatar.vue'

const emit = defineEmits(['created'])
const content = ref('')
const file = ref(null)
const previewUrl = ref('')
const kind = ref('')
const submitting = ref(false)
const fileInput = ref(null)
const videoInput = ref(null)

function pick(k) {
  kind.value = k
  if (k === 'image') fileInput.value?.click()
  else videoInput.value?.click()
}

function onFile(e) {
  const f = e.target.files?.[0]
  if (!f) return
  file.value = f
  previewUrl.value = URL.createObjectURL(f)
  e.target.value = ''
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = null
  previewUrl.value = ''
  kind.value = ''
}

async function submit() {
  if (!store.token) { notify('请先登录', 'error'); return }
  if (!content.value.trim() && !file.value) { notify('写点什么或选个文件吧', 'error'); return }
  submitting.value = true
  try {
    let mediaUrl = ''
    let mediaType = ''
    if (file.value) {
      const up = await api.upload(file.value)
      mediaUrl = up.url
      mediaType = up.media_type
    }
    const post = await api.post('/posts', {
      content: content.value.trim(),
      media_url: mediaUrl,
      media_type: mediaType
    })
    content.value = ''
    clearFile()
    emit('created', post)
    if (post.status === 'pending') {
      notify('已提交，内容进入审核队列', 'info')
    } else {
      notify('发布成功', 'success')
    }
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="composer card">
    <div class="composer-top">
      <Avatar :name="store.user?.display_name || store.user?.username || '?'" :size="40" />
      <textarea
        v-model="content"
        class="composer-input"
        maxlength="5000"
        placeholder="分享你的校园生活，或者……试试发一条广告？"
      ></textarea>
    </div>

    <div v-if="previewUrl" class="preview">
      <img v-if="kind === 'image'" :src="previewUrl" alt="预览" />
      <video v-else :src="previewUrl" controls></video>
      <button class="remove" @click="clearFile">×</button>
    </div>

    <div class="composer-foot">
      <div class="tools">
        <button class="tool" @click="pick('image')">🖼 图片</button>
        <button class="tool" @click="pick('video')">🎬 视频</button>
        <span class="muted small">{{ content.length }} / 5000</span>
      </div>
      <button class="btn btn-primary" :disabled="submitting" @click="submit">
        <span v-if="submitting" class="spinner"></span>
        {{ submitting ? '发布中' : '发布' }}
      </button>
    </div>

    <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFile" />
    <input ref="videoInput" type="file" accept="video/*" class="hidden" @change="onFile" />
  </div>
</template>

<style scoped>
.composer { padding: 16px 18px; }
.composer-top { display: flex; gap: 12px; }
.composer-input {
  flex: 1; border: 0; outline: none; resize: none; min-height: 74px;
  font-size: 15px; line-height: 1.7; font-family: inherit; background: transparent;
}
.preview { position: relative; margin: 10px 0 0 52px; max-width: 320px; }
.preview img, .preview video { width: 100%; border-radius: 10px; max-height: 220px; object-fit: cover; background: #000; }
.remove {
  position: absolute; top: 6px; right: 6px; width: 24px; height: 24px; border-radius: 50%;
  border: 0; background: rgba(0, 0, 0, .55); color: #fff; cursor: pointer; font-size: 15px; line-height: 1;
}
.composer-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--line); }
.tools { display: flex; align-items: center; gap: 8px; }
.tool { border: 1px solid var(--line); background: #fff; border-radius: 999px; padding: 5px 12px; cursor: pointer; font-size: 12px; color: var(--muted); }
.tool:hover { color: var(--primary); border-color: var(--primary); }
</style>

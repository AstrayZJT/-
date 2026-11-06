<script setup>
import { onMounted, ref } from 'vue'
import { api, timeAgo } from '../../api'
import { notify } from '../../store'

const tab = ref('pending')
const items = ref([])
const loading = ref(false)

const tabs = [
  { key: 'pending', label: '待审核' },
  { key: 'approved', label: '已通过' },
  { key: 'rejected', label: '未通过' }
]

async function load() {
  loading.value = true
  try {
    items.value = await api.get(`/admin/moderation?status=${tab.value}&limit=50`)
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  tab.value = key
  load()
}

async function review(item, action) {
  try {
    await api.post(`/admin/moderation/${item.id}/review`, { action })
    notify(action === 'approve' ? '已通过' : '已驳回', 'success')
    items.value = items.value.filter((i) => i.id !== item.id)
  } catch (e) {
    notify(e.message, 'error')
  }
}

onMounted(load)
</script>

<template>
  <div class="stack">
    <header class="row-between">
      <div>
        <h1>审核队列</h1>
        <p class="muted small" style="margin: 4px 0 0">模型给出初判，人工做最终处置；所有操作留痕</p>
      </div>
      <button class="btn btn-sm" @click="load">刷新</button>
    </header>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" class="tab" :class="{ active: tab === t.key }" @click="switchTab(t.key)">
        {{ t.label }}
      </button>
    </div>

    <div v-if="loading" class="card skeleton" style="height: 120px"></div>
    <div v-else-if="!items.length" class="empty card">
      <div style="font-size: 30px">🎉</div>
      当前没有{{ tab === 'pending' ? '待审核' : '相关' }}内容
    </div>

    <div v-else class="stack">
      <article v-for="item in items" :key="item.id" class="card review-card">
        <div class="review-main">
          <div class="row wrap" style="gap: 8px">
            <span class="badge" :class="item.label === 'ad' ? 'badge-ad' : item.label === 'abuse' ? 'badge-abuse' : 'badge-ok'">
              {{ item.label === 'ad' ? '广告导流' : item.label === 'abuse' ? '辱骂攻击' : '正常' }}
            </span>
            <span class="badge">{{ item.modality === 'text' ? '文本' : item.modality === 'image' ? '图片' : '视频' }}</span>
            <span class="muted small">置信度 {{ (item.score * 100).toFixed(1) }}%</span>
            <span class="muted small">· {{ timeAgo(item.created_at) }}</span>
          </div>
          <p class="review-text">{{ item.post.content || '[媒体内容]' }}</p>
          <div class="reason">{{ item.reason }}</div>
          <div class="review-meta muted small">
            作者：{{ item.post.author.display_name || item.post.author.username }}
            <span v-if="item.post.author.is_bot" class="badge badge-bot" style="margin-left: 6px">BOT</span>
          </div>
        </div>

        <div v-if="item.post.media_type === 'image'" class="thumb">
          <img :src="item.post.media_url" alt="" />
        </div>
        <div v-else-if="item.post.media_type === 'video'" class="thumb">
          <video :src="item.post.media_url" controls></video>
        </div>

        <div v-if="item.status === 'pending'" class="review-actions">
          <button class="btn btn-ok btn-sm" @click="review(item, 'approve')">通过</button>
          <button class="btn btn-danger btn-sm" @click="review(item, 'reject')">驳回</button>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.review-card { padding: 16px; display: flex; gap: 16px; align-items: flex-start; }
.review-main { flex: 1; min-width: 0; }
.review-text { font-size: 15px; margin: 10px 0 8px; white-space: pre-wrap; word-break: break-word; }
.reason { font-size: 12px; background: #fff8ec; color: #8a5a00; border-radius: 8px; padding: 7px 10px; display: inline-block; }
.review-meta { margin-top: 8px; }
.thumb { width: 140px; flex: none; }
.thumb img, .thumb video { width: 100%; border-radius: 10px; display: block; max-height: 110px; object-fit: cover; background: #000; }
.review-actions { display: flex; flex-direction: column; gap: 6px; flex: none; }
@media (max-width: 760px) {
  .review-card { flex-wrap: wrap; }
  .thumb { width: 100%; order: 3; }
  .review-actions { flex-direction: row; width: 100%; }
}
</style>

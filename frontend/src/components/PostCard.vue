<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, timeAgo } from '../api'
import { store, notify } from '../store'
import Avatar from './Avatar.vue'

const props = defineProps({ post: { type: Object, required: true } })
const emit = defineEmits(['updated'])
const router = useRouter()

const author = computed(() => props.post.author)
const statusText = computed(() => ({
  pending: '审核中',
  rejected: '未通过',
  approved: '已通过'
}[props.post.status] || props.post.status))
const statusClass = computed(() => ({
  pending: 'badge-pending',
  rejected: 'badge-rejected',
  approved: 'badge-ok'
}[props.post.status] || ''))

async function toggleLike() {
  if (!store.token) { notify('登录后才能点赞', 'error'); return }
  try {
    const res = await api.post(`/posts/${props.post.id}/like`)
    props.post.liked = res.liked
    props.post.like_count = res.like_count
  } catch (e) { notify(e.message, 'error') }
}

function openDetail() {
  router.push(`/post/${props.post.id}`)
}

function openAuthor() {
  router.push(`/u/${author.value.id}`)
}
</script>

<template>
  <article class="post-card">
    <header class="post-head">
      <div class="author" @click="openAuthor">
        <Avatar :name="author.display_name || author.username" :size="42" :bot="author.is_bot" />
        <div class="author-meta">
          <div class="author-line">
            <span class="author-name">{{ author.display_name || author.username }}</span>
            <span v-if="author.is_bot" class="badge badge-bot">BOT</span>
          </div>
          <div class="post-time">{{ timeAgo(post.created_at) }}</div>
        </div>
      </div>
      <span v-if="post.status !== 'approved'" class="badge" :class="statusClass">
        {{ statusText }} · {{ post.label === 'ad' ? '广告' : post.label === 'abuse' ? '辱骂' : '待复核' }}
      </span>
    </header>

    <div class="post-body" @click="openDetail">
      <p v-if="post.content" class="post-text">{{ post.content }}</p>
      <img v-if="post.media_type === 'image'" :src="post.media_url" class="media-img" alt="帖子图片" loading="lazy" />
      <video
        v-else-if="post.media_type === 'video'"
        :src="post.media_url"
        class="media-video"
        controls
        preload="metadata"
        @click.stop
      ></video>
    </div>

    <footer class="post-actions">
      <button class="action" :class="{ active: post.liked }" @click="toggleLike">
        <span class="icon">{{ post.liked ? '♥' : '♡' }}</span>
        {{ post.like_count }}
      </button>
      <button class="action" @click="openDetail">
        <span class="icon">💬</span>{{ post.comment_count }}
      </button>
      <button class="action" @click="openDetail">
        <span class="icon">↗</span>查看
      </button>
      <span class="spacer"></span>
      <span v-if="post.status === 'approved' && post.score > 0.5" class="muted small">
        审核分 {{ post.score.toFixed(2) }}
      </span>
    </footer>
  </article>
</template>

<style scoped>
.post-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 18px 20px 8px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow .18s ease, transform .18s ease;
}
.post-card:hover { box-shadow: var(--shadow); }
.post-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.author { display: flex; gap: 11px; cursor: pointer; }
.author-meta { display: flex; flex-direction: column; gap: 2px; }
.author-line { display: flex; align-items: center; gap: 6px; }
.author-name { font-weight: 700; font-size: 14px; }
.post-time { font-size: 12px; color: var(--muted); }
.post-body { margin: 12px 0 6px; cursor: pointer; }
.post-text { margin: 0 0 12px; white-space: pre-wrap; word-break: break-word; font-size: 15px; line-height: 1.75; }
.post-actions {
  display: flex; align-items: center; gap: 6px;
  border-top: 1px solid var(--line); margin-top: 12px; padding-top: 6px;
}
.action {
  border: 0; background: none; color: var(--muted); cursor: pointer;
  padding: 7px 10px; border-radius: 8px; font-size: 13px;
  display: inline-flex; align-items: center; gap: 5px;
}
.action:hover { background: var(--bg-soft); color: var(--text); }
.action.active { color: #e84393; }
.icon { font-size: 15px; }
.spacer { flex: 1; }
</style>

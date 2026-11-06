<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, timeAgo } from '../api'
import { store, notify } from '../store'
import Avatar from '../components/Avatar.vue'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const comments = ref([])
const draft = ref('')
const loading = ref(true)
const sending = ref(false)

const canSeeModeration = computed(() =>
  store.user && (store.user.is_admin || store.user.id === post.value?.author?.id)
)

async function load() {
  loading.value = true
  try {
    post.value = await api.get(`/posts/${route.params.id}`)
    comments.value = await api.get(`/posts/${route.params.id}/comments`)
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function toggleLike() {
  if (!store.token) { notify('登录后才能点赞', 'error'); return }
  const res = await api.post(`/posts/${post.value.id}/like`)
  post.value.liked = res.liked
  post.value.like_count = res.like_count
}

async function sendComment() {
  if (!store.token) { notify('登录后才能评论', 'error'); return }
  if (!draft.value.trim()) return
  sending.value = true
  try {
    const c = await api.post(`/posts/${post.value.id}/comments`, { content: draft.value.trim() })
    if (c.status === 'rejected') {
      notify('评论包含违规内容，已被拦截', 'error')
    } else {
      comments.value.push(c)
      post.value.comment_count += 1
      draft.value = ''
    }
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    sending.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="detail-wrap">
    <button class="btn btn-sm back" @click="router.back()">← 返回</button>

    <div v-if="loading" class="card skeleton" style="height: 240px"></div>

    <template v-else-if="post">
      <article class="card detail-card">
        <header class="detail-head">
          <router-link :to="`/u/${post.author.id}`" class="author-link">
            <Avatar :name="post.author.display_name || post.author.username" :size="46" :bot="post.author.is_bot" />
            <div>
              <div class="row" style="gap: 6px">
                <strong>{{ post.author.display_name || post.author.username }}</strong>
                <span v-if="post.author.is_bot" class="badge badge-bot">BOT</span>
              </div>
              <div class="muted small">{{ timeAgo(post.created_at) }}</div>
            </div>
          </router-link>
          <span class="badge" :class="post.status === 'pending' ? 'badge-pending' : post.status === 'rejected' ? 'badge-rejected' : 'badge-ok'">
            {{ post.status === 'pending' ? '审核中' : post.status === 'rejected' ? '未通过' : '已通过' }}
          </span>
        </header>

        <p v-if="post.content" class="detail-text">{{ post.content }}</p>
        <img v-if="post.media_type === 'image'" :src="post.media_url" class="media-img" alt="" />
        <video v-else-if="post.media_type === 'video'" :src="post.media_url" class="media-video" controls></video>

        <div v-if="canSeeModeration && post.status !== 'approved'" class="mod-hint">
          审核结论：<b>{{ post.label === 'ad' ? '广告导流' : post.label === 'abuse' ? '辱骂攻击' : post.label }}</b>
          ，置信度 {{ (post.score * 100).toFixed(1) }}%。管理员可在后台复核。
        </div>

        <footer class="detail-actions">
          <button class="btn" :class="{ 'btn-primary': post.liked }" @click="toggleLike">
            {{ post.liked ? '♥ 已赞' : '♡ 点赞' }} {{ post.like_count }}
          </button>
          <span class="muted small">{{ post.comment_count }} 条评论</span>
        </footer>
      </article>

      <section class="card comments">
        <h3>评论 {{ post.comment_count }}</h3>
        <div v-if="store.token" class="comment-form">
          <input
            v-model="draft"
            class="input"
            placeholder="友善评论，系统会自动审核"
            @keyup.enter="sendComment"
          />
          <button class="btn btn-primary" :disabled="sending" @click="sendComment">
            <span v-if="sending" class="spinner"></span>发送
          </button>
        </div>
        <div v-else class="muted small">
          <router-link to="/login">登录</router-link> 后参与评论
        </div>

        <div v-if="!comments.length" class="empty" style="padding: 26px">还没有评论</div>
        <ul v-else class="comment-list">
          <li v-for="c in comments" :key="c.id" class="comment">
            <Avatar :name="c.user.display_name || c.user.username" :size="32" :bot="c.user.is_bot" />
            <div class="comment-body">
              <div class="row" style="gap: 6px">
                <strong class="small">{{ c.user.display_name || c.user.username }}</strong>
                <span class="muted small">{{ timeAgo(c.created_at) }}</span>
              </div>
              <div>{{ c.content }}</div>
            </div>
          </li>
        </ul>
      </section>
    </template>

    <div v-else class="empty card">帖子不存在或已被删除</div>
  </div>
</template>

<style scoped>
.detail-wrap { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 14px; }
.back { align-self: flex-start; }
.detail-card { padding: 20px; }
.detail-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.author-link { display: flex; gap: 12px; color: inherit; }
.detail-text { font-size: 16px; line-height: 1.8; white-space: pre-wrap; margin: 16px 0; }
.mod-hint {
  margin-top: 14px; background: #fff8ec; border: 1px solid #ffe2b0; color: #8a5a00;
  padding: 10px 12px; border-radius: 10px; font-size: 13px;
}
.detail-actions { display: flex; align-items: center; gap: 14px; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--line); }
.comments { padding: 18px 20px; }
.comments h3 { margin-bottom: 12px; }
.comment-form { display: flex; gap: 8px; margin-bottom: 14px; }
.comment-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 14px; }
.comment { display: flex; gap: 10px; }
.comment-body { background: var(--bg-soft); border-radius: 10px; padding: 8px 12px; flex: 1; }
</style>

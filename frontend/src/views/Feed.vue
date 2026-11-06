<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { store } from '../store'
import Composer from '../components/Composer.vue'
import PostCard from '../components/PostCard.vue'

const route = useRoute()
const router = useRouter()
const posts = ref([])
const total = ref(0)
const page = ref(1)
const sort = ref('latest')
const loading = ref(false)
const loadingMore = ref(false)
const pageSize = 10

const q = computed(() => (route.query.q || '').toString())

async function load(reset = true) {
  if (reset) {
    page.value = 1
    loading.value = true
  } else {
    loadingMore.value = true
  }
  try {
    const params = new URLSearchParams({
      sort: sort.value,
      page: String(page.value),
      size: String(pageSize)
    })
    if (q.value) params.set('q', q.value)
    const data = await api.get(`/posts?${params.toString()}`)
    posts.value = reset ? data.items : [...posts.value, ...data.items]
    total.value = data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function switchSort(value) {
  if (sort.value === value) return
  sort.value = value
  load()
}

function loadMore() {
  page.value += 1
  load(false)
}

function onCreated(post) {
  if (post.status === 'approved') {
    posts.value.unshift(post)
    total.value += 1
  } else {
    router.push(`/post/${post.id}`)
  }
}

function clearSearch() {
  router.push('/')
}

onMounted(() => load())
watch(() => route.query.q, () => load())
</script>

<template>
  <div class="feed-layout">
    <div class="feed-main">
      <div v-if="q" class="search-banner card">
        <div>
          搜索 <strong>“{{ q }}”</strong>，共 {{ total }} 条结果
        </div>
        <button class="btn btn-sm" @click="clearSearch">清除</button>
      </div>

      <Composer v-if="store.token" @created="onCreated" />
      <div v-else class="login-cta card">
        <div>
          <strong>登录后参与互动</strong>
          <div class="muted small">发帖、点赞、评论，或进入管理后台体验水军模拟与攻防实验。</div>
        </div>
        <router-link to="/login" class="btn btn-primary btn-sm">去登录</router-link>
      </div>

      <div class="feed-toolbar">
        <div class="tabs">
          <button class="tab" :class="{ active: sort === 'latest' }" @click="switchSort('latest')">最新</button>
          <button class="tab" :class="{ active: sort === 'hot' }" @click="switchSort('hot')">最热</button>
        </div>
        <span class="muted small">{{ total }} 条动态</span>
      </div>

      <div v-if="loading" class="stack">
        <div v-for="i in 3" :key="i" class="card skeleton-card">
          <div class="skeleton" style="width: 42px; height: 42px; border-radius: 50%"></div>
          <div class="grow">
            <div class="skeleton" style="width: 120px; height: 12px; margin-bottom: 8px"></div>
            <div class="skeleton" style="width: 90%; height: 12px; margin-bottom: 6px"></div>
            <div class="skeleton" style="width: 70%; height: 12px"></div>
          </div>
        </div>
      </div>

      <div v-else-if="!posts.length" class="empty card">
        <div style="font-size: 34px; margin-bottom: 8px">🫧</div>
        还没有动态，来发第一条吧
      </div>

      <div v-else class="stack">
        <PostCard v-for="post in posts" :key="post.id" :post="post" />
        <button v-if="posts.length < total" class="btn load-more" :disabled="loadingMore" @click="loadMore">
          <span v-if="loadingMore" class="spinner"></span>
          {{ loadingMore ? '加载中' : '加载更多' }}
        </button>
      </div>
    </div>

    <aside class="feed-side">
      <div class="card side-card">
        <h3>演示指引</h3>
        <ol class="guide">
          <li><b>普通用户</b>：发一条图文或短视频，观察是否进入审核。</li>
          <li><b>管理员</b>：到「水军模拟」建 20 个 bot 刷一条帖子。</li>
          <li><b>攻防实验室</b>：用同音字绕过审核，再切换防御等级。</li>
        </ol>
        <router-link v-if="store.user?.is_admin" to="/admin/dashboard" class="btn btn-sm side-btn">
          进入管理后台
        </router-link>
      </div>

      <div class="card side-card">
        <h3>热门话题</h3>
        <div class="tags">
          <span># 校园日常</span>
          <span># 期末周</span>
          <span># 食堂测评</span>
          <span># 考研加油</span>
          <span># 秦岭徒步</span>
        </div>
      </div>

      <div class="card side-card muted small">
        本平台为《应用综合实验》课程演示，账号、内容与互动均由脚本合成，不接入任何真实社交平台。
      </div>
    </aside>
  </div>
</template>

<style scoped>
.feed-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 20px; align-items: start; }
.feed-main { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.feed-side { display: flex; flex-direction: column; gap: 14px; position: sticky; top: 80px; }
.search-banner { padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; }
.login-cta { padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.feed-toolbar { display: flex; align-items: center; justify-content: space-between; }
.skeleton-card { padding: 18px; display: flex; gap: 12px; }
.load-more { width: 100%; padding: 12px; }
.side-card { padding: 16px; }
.side-card h3 { font-size: 14px; margin-bottom: 10px; }
.guide { margin: 0; padding-left: 18px; color: var(--muted); font-size: 13px; line-height: 1.9; }
.guide b { color: var(--text); }
.side-btn { width: 100%; margin-top: 10px; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tags span {
  background: var(--bg-soft); border-radius: 999px; padding: 5px 11px; font-size: 12px; color: var(--muted);
}
@media (max-width: 960px) {
  .feed-layout { grid-template-columns: 1fr; }
  .feed-side { position: static; order: 2; }
}
</style>

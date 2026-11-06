<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { store, notify, setAuth } from '../store'
import Avatar from '../components/Avatar.vue'
import PostCard from '../components/PostCard.vue'

const route = useRoute()
const user = ref(null)
const posts = ref([])
const loading = ref(true)
const editing = ref(false)
const editName = ref('')
const editBio = ref('')

const isSelf = computed(() => store.user && user.value && store.user.id === user.value.id)

async function load() {
  loading.value = true
  try {
    user.value = await api.get(`/users/${route.params.id}`)
    posts.value = await api.get(`/users/${route.params.id}/posts`)
    editName.value = user.value.display_name
    editBio.value = user.value.bio
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function toggleFollow() {
  if (!store.token) { notify('请先登录', 'error'); return }
  try {
    if (user.value.is_following) {
      await api.del(`/users/${user.value.id}/follow`)
      user.value.is_following = false
      user.value.followers = Math.max(0, user.value.followers - 1)
    } else {
      await api.post(`/users/${user.value.id}/follow`)
      user.value.is_following = true
      user.value.followers += 1
    }
  } catch (e) { notify(e.message, 'error') }
}

async function saveProfile() {
  try {
    const updated = await api.patch('/auth/me', { display_name: editName.value, bio: editBio.value })
    user.value = { ...user.value, ...updated }
    setAuth(store.token, updated)
    editing.value = false
    notify('资料已更新', 'success')
  } catch (e) { notify(e.message, 'error') }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <div v-if="loading" class="card skeleton" style="height: 200px"></div>

  <div v-else-if="user" class="profile-wrap">
    <section class="card profile-head">
      <div class="profile-bg"></div>
      <div class="profile-main">
        <Avatar :name="user.display_name || user.username" :size="76" :bot="user.is_bot" />
        <div class="profile-info">
          <div class="row" style="gap: 8px">
            <h1>{{ user.display_name || user.username }}</h1>
            <span v-if="user.is_bot" class="badge badge-bot">BOT</span>
            <span v-if="user.is_admin" class="badge">管理员</span>
          </div>
          <div class="muted">@{{ user.username }}</div>
          <p class="bio">{{ user.bio || '这个人很懒，还没有填写简介。' }}</p>
          <div class="stats">
            <span><b>{{ user.post_count }}</b> 动态</span>
            <span><b>{{ user.followers }}</b> 粉丝</span>
            <span><b>{{ user.following }}</b> 关注</span>
          </div>
        </div>
        <div class="profile-actions">
          <button v-if="isSelf" class="btn" @click="editing = !editing">编辑资料</button>
          <button
            v-else-if="store.token"
            class="btn"
            :class="user.is_following ? '' : 'btn-primary'"
            @click="toggleFollow"
          >
            {{ user.is_following ? '已关注' : '+ 关注' }}
          </button>
        </div>
      </div>

      <div v-if="editing" class="edit-box">
        <div class="field">
          <label>昵称</label>
          <input v-model="editName" class="input" maxlength="30" />
        </div>
        <div class="field">
          <label>简介</label>
          <textarea v-model="editBio" class="textarea" maxlength="200"></textarea>
        </div>
        <div class="row">
          <button class="btn btn-primary" @click="saveProfile">保存</button>
          <button class="btn" @click="editing = false">取消</button>
        </div>
      </div>
    </section>

    <section class="stack">
      <h2 class="section-title">TA 的动态</h2>
      <div v-if="!posts.length" class="empty card">还没有发布动态</div>
      <PostCard v-for="post in posts" :key="post.id" :post="post" />
    </section>
  </div>
</template>

<style scoped>
.profile-wrap { max-width: 760px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }
.profile-head { overflow: hidden; }
.profile-bg {
  height: 96px;
  background: linear-gradient(120deg, #6c5ce7, #a29bfe 45%, #ff7675);
}
.profile-main { padding: 0 22px 18px; display: flex; gap: 16px; margin-top: -34px; align-items: flex-end; }
.profile-info { flex: 1; }
.profile-info h1 { font-size: 22px; }
.bio { margin: 8px 0; color: var(--muted); font-size: 13px; }
.stats { display: flex; gap: 18px; font-size: 13px; color: var(--muted); }
.stats b { color: var(--text); }
.profile-actions { align-self: flex-end; padding-bottom: 4px; }
.edit-box { padding: 0 22px 20px; border-top: 1px solid var(--line); padding-top: 16px; }
.section-title { font-size: 16px; }
</style>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { store, clearAuth } from './store'
import Avatar from './components/Avatar.vue'

const router = useRouter()
const route = useRoute()
const q = ref(route.query.q || '')
const menuOpen = ref(false)

const user = computed(() => store.user)

function search() {
  router.push({ path: '/', query: q.value ? { q: q.value } : {} })
}

function logout() {
  clearAuth()
  menuOpen.value = false
  router.push('/login')
}
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <router-link to="/" class="brand">
        <span class="brand-mark">S</span>
        <span class="brand-name">SocialSim</span>
        <span class="brand-tag">拟真社交</span>
      </router-link>

      <div class="search">
        <input
          v-model="q"
          class="search-input"
          placeholder="搜索动态、话题……"
          @keyup.enter="search"
        />
        <button class="search-btn" @click="search">搜索</button>
      </div>

      <nav class="nav">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link v-if="user?.is_admin" to="/admin/dashboard" class="nav-link admin-link">
          管理后台
        </router-link>

        <template v-if="user">
          <div class="user-menu" @click="menuOpen = !menuOpen">
            <Avatar :name="user.display_name || user.username" :size="34" />
            <span class="user-name">{{ user.display_name || user.username }}</span>
            <span class="caret">▾</span>
            <div v-if="menuOpen" class="dropdown" @click.stop>
              <router-link :to="`/u/${user.id}`" class="dropdown-item" @click="menuOpen = false">
                个人主页
              </router-link>
              <button class="dropdown-item danger" @click="logout">退出登录</button>
            </div>
          </div>
        </template>
        <router-link v-else to="/login" class="btn btn-primary btn-sm">登录 / 注册</router-link>
      </nav>
    </div>
  </header>

  <main :class="route.path === '/login' ? 'login-shell' : 'page'">
    <router-view />
  </main>

  <transition name="toast">
    <div v-if="store.toast" class="toast" :class="`toast-${store.toast.type}`">
      {{ store.toast.message }}
    </div>
  </transition>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(255, 255, 255, .86);
  backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--line);
}
.topbar-inner {
  max-width: 1120px;
  margin: 0 auto;
  height: 62px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 18px;
}
.brand { display: flex; align-items: center; gap: 8px; text-decoration: none; color: inherit; }
.brand-mark {
  width: 34px; height: 34px; border-radius: 10px;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: #fff; font-weight: 800; display: grid; place-items: center;
  box-shadow: 0 6px 14px rgba(108, 92, 231, .28);
}
.brand-name { font-weight: 800; font-size: 18px; letter-spacing: .2px; }
.brand-tag { font-size: 11px; color: var(--muted); border: 1px solid var(--line); padding: 2px 6px; border-radius: 999px; }
.search { flex: 1; max-width: 420px; display: flex; background: var(--bg-soft); border-radius: 999px; padding: 4px; }
.search-input { flex: 1; border: 0; background: transparent; padding: 8px 14px; outline: none; font-size: 14px; }
.search-btn { border: 0; background: #fff; border-radius: 999px; padding: 7px 14px; cursor: pointer; font-size: 13px; color: var(--text); box-shadow: var(--shadow-sm); }
.nav { margin-left: auto; display: flex; align-items: center; gap: 16px; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 14px; }
.nav-link.router-link-active { color: var(--primary); font-weight: 600; }
.admin-link { color: #6c5ce7; }
.user-menu { position: relative; display: flex; align-items: center; gap: 8px; cursor: pointer; }
.user-name { font-size: 13px; max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.caret { font-size: 10px; color: var(--muted); }
.dropdown {
  position: absolute; right: 0; top: 44px; background: #fff; border-radius: 12px;
  box-shadow: var(--shadow-lg); padding: 6px; min-width: 140px; border: 1px solid var(--line);
}
.dropdown-item {
  display: block; width: 100%; text-align: left; padding: 9px 12px; border: 0; background: none;
  border-radius: 8px; cursor: pointer; font-size: 13px; color: var(--text); text-decoration: none;
}
.dropdown-item:hover { background: var(--bg-soft); }
.dropdown-item.danger { color: #d63031; }
.toast {
  position: fixed; left: 50%; bottom: 36px; transform: translateX(-50%);
  background: #2d3436; color: #fff; padding: 11px 20px; border-radius: 12px;
  font-size: 14px; box-shadow: var(--shadow-lg); z-index: 50;
}
.toast-success { background: #00b894; }
.toast-error { background: #d63031; }
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }
@media (max-width: 760px) {
  .brand-tag, .search { display: none; }
  .topbar-inner { gap: 10px; }
}
</style>

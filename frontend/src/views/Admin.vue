<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const stats = ref(null)
const settings = ref(null)

const nav = [
  { to: '/admin/dashboard', label: '运营概览', icon: '📊' },
  { to: '/admin/moderation', label: '审核队列', icon: '🛡️' },
  { to: '/admin/bots', label: '水军模拟', icon: '🤖' },
  { to: '/admin/lab', label: '攻防实验室', icon: '⚔️' },
  { to: '/admin/settings', label: '防御设置', icon: '⚙️' }
]

onMounted(async () => {
  try {
    const [s, st] = await Promise.all([api.get('/admin/stats'), api.get('/admin/settings')])
    stats.value = s
    settings.value = st
  } catch (e) {
    console.error(e)
  }
})
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-side card">
      <div class="admin-title">
        <div class="dot"></div>
        <div>
          <div class="admin-name">管理后台</div>
          <div class="muted small">内容安全运营台</div>
        </div>
      </div>
      <nav class="admin-nav">
        <router-link v-for="item in nav" :key="item.to" :to="item.to" class="admin-link">
          <span class="icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
          <span v-if="item.to === '/admin/moderation' && stats?.pending" class="count">{{ stats.pending }}</span>
        </router-link>
      </nav>
      <div class="admin-foot">
        <div class="level-pill">
          防御等级 {{ settings?.defense_level ?? '-' }}
          <span class="muted small">{{ settings?.levels?.[settings?.defense_level] || '' }}</span>
        </div>
        <router-link to="/admin/settings" class="btn btn-sm" style="width: 100%">调整防御</router-link>
      </div>
    </aside>

    <section class="admin-main">
      <router-view />
    </section>
  </div>
</template>

<style scoped>
.admin-layout { display: grid; grid-template-columns: 228px minmax(0, 1fr); gap: 18px; align-items: start; }
.admin-side { padding: 16px; position: sticky; top: 80px; display: flex; flex-direction: column; gap: 16px; }
.admin-title { display: flex; gap: 10px; align-items: center; padding: 4px 6px 12px; border-bottom: 1px solid var(--line); }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #00b894; box-shadow: 0 0 0 4px rgba(0, 184, 148, .15); }
.admin-name { font-weight: 800; }
.admin-nav { display: flex; flex-direction: column; gap: 4px; }
.admin-link {
  display: flex; align-items: center; gap: 10px; padding: 9px 11px; border-radius: 10px;
  color: var(--muted); font-size: 13px;
}
.admin-link:hover { background: var(--bg-soft); }
.admin-link.router-link-active { background: #f0edff; color: var(--primary); font-weight: 600; }
.icon { width: 18px; text-align: center; }
.count {
  margin-left: auto; background: #ffecec; color: var(--danger); font-size: 11px;
  border-radius: 999px; padding: 1px 7px; font-weight: 700;
}
.admin-foot { border-top: 1px solid var(--line); padding-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.level-pill { font-size: 12px; display: flex; flex-direction: column; gap: 2px; }
.admin-main { min-width: 0; }
@media (max-width: 900px) {
  .admin-layout { grid-template-columns: 1fr; }
  .admin-side { position: static; }
  .admin-nav { flex-direction: row; overflow-x: auto; }
  .admin-link { white-space: nowrap; }
  .admin-foot { display: none; }
}
</style>

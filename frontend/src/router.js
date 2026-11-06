import { createRouter, createWebHistory } from 'vue-router'
import { store } from './store'

import Feed from './views/Feed.vue'
import Login from './views/Login.vue'
import PostDetail from './views/PostDetail.vue'
import Profile from './views/Profile.vue'
import Admin from './views/Admin.vue'
import AdminDashboard from './views/admin/Dashboard.vue'
import AdminModeration from './views/admin/Moderation.vue'
import AdminBots from './views/admin/Bots.vue'
import AdminLab from './views/admin/Lab.vue'
import AdminSettings from './views/admin/Settings.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/', component: Feed },
  { path: '/post/:id', component: PostDetail },
  { path: '/u/:id', component: Profile },
  {
    path: '/admin',
    component: Admin,
    meta: { admin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', component: AdminDashboard },
      { path: 'moderation', component: AdminModeration },
      { path: 'bots', component: AdminBots },
      { path: 'lab', component: AdminLab },
      { path: 'settings', component: AdminSettings }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to) => {
  if (to.meta.admin && !store.user?.is_admin) return '/login'
  if (to.path === '/login' && store.token) return '/'
  return true
})

export default router

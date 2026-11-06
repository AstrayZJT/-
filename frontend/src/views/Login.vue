<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { setAuth, notify } from '../store'

const router = useRouter()
const mode = ref('login')
const username = ref('')
const password = ref('')
const displayName = ref('')
const loading = ref(false)

async function submit() {
  if (loading.value) return
  loading.value = true
  try {
    const path = mode.value === 'login' ? '/auth/login' : '/auth/register'
    const body = mode.value === 'login'
      ? { username: username.value, password: password.value }
      : { username: username.value, password: password.value, display_name: displayName.value }
    const data = await api.post(path, body)
    setAuth(data.access_token, data.user)
    notify(mode.value === 'login' ? '登录成功' : '注册成功，欢迎加入', 'success')
    router.push('/')
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

function fill(name, pwd) {
  username.value = name
  password.value = pwd
  mode.value = 'login'
}
</script>

<template>
  <div class="login-page">
    <section class="hero">
      <div class="hero-badge">应用综合实验 · 课程项目</div>
      <h1>SocialSim<br />社交网络拟真平台</h1>
      <p class="hero-sub">
        一个可运行、可演示的社交产品原型，内置水军行为模拟、多模态内容审核与 AI 攻防靶场。
      </p>
      <ul class="hero-list">
        <li><span>01</span> 图文 / 短视频信息流与社交互动</li>
        <li><span>02</span> 水军账号批量注册与协同刷屏</li>
        <li><span>03</span> 文本 / 图片 / 视频不良内容监测</li>
        <li><span>04</span> 对抗样本攻击与防御对比实验</li>
      </ul>
      <div class="hero-foot">西北工业大学 · 光电与智能研究院 · 2026</div>
    </section>

    <section class="panel">
      <div class="panel-card">
        <div class="tabs">
          <button class="tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button class="tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
        </div>

        <h2>{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</h2>
        <p class="muted small">
          {{ mode === 'login' ? '登录后即可发帖、互动，或进入管理后台。' : '注册一个普通用户，体验完整社交功能。' }}
        </p>

        <form class="stack" @submit.prevent="submit">
          <div class="field">
            <label>用户名</label>
            <input v-model="username" class="input" placeholder="3-20 位字母、数字或中文" autocomplete="username" />
          </div>
          <div v-if="mode === 'register'" class="field">
            <label>昵称（选填）</label>
            <input v-model="displayName" class="input" placeholder="展示在主页的名字" />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="password" type="password" class="input" placeholder="至少 6 位" autocomplete="current-password" />
          </div>
          <button class="btn btn-primary btn-lg" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            {{ mode === 'login' ? '登录' : '注册并登录' }}
          </button>
        </form>

        <div class="demo">
          <div class="demo-title">演示账号（点击填充）</div>
          <div class="demo-row">
            <button class="demo-chip" @click="fill('linxiaoyu', 'user123')">普通用户 linxiaoyu / user123</button>
            <button class="demo-chip admin" @click="fill('admin', 'admin123')">管理员 admin / admin123</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: calc(100vh - 62px);
  display: grid;
  grid-template-columns: 1.15fr .85fr;
  gap: 0;
  margin: 0;
}
.hero {
  padding: 74px 64px;
  background:
    radial-gradient(900px 420px at 10% 0%, rgba(140, 122, 230, .5), transparent 60%),
    radial-gradient(700px 400px at 90% 90%, rgba(255, 118, 117, .28), transparent 60%),
    linear-gradient(150deg, #2b2a55 0%, #1d1c33 55%, #141322 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
}
.hero-badge {
  align-self: flex-start;
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, .25);
  padding: 4px 12px;
  border-radius: 999px;
  color: rgba(255, 255, 255, .8);
  letter-spacing: .5px;
}
.hero h1 { font-size: 46px; line-height: 1.18; margin: 26px 0 18px; letter-spacing: -.5px; }
.hero-sub { color: rgba(255, 255, 255, .72); font-size: 15px; max-width: 460px; line-height: 1.8; }
.hero-list { list-style: none; padding: 0; margin: 34px 0 0; display: flex; flex-direction: column; gap: 14px; }
.hero-list li { display: flex; align-items: center; gap: 12px; color: rgba(255, 255, 255, .88); font-size: 14px; }
.hero-list span {
  font-family: monospace; font-size: 11px; color: #b9b3ff;
  border: 1px solid rgba(185, 179, 255, .4); border-radius: 6px; padding: 2px 7px;
}
.hero-foot { margin-top: auto; color: rgba(255, 255, 255, .35); font-size: 12px; letter-spacing: .5px; }
.panel { display: grid; place-items: center; padding: 40px; }
.panel-card { width: 100%; max-width: 380px; }
.panel-card h2 { margin: 22px 0 6px; font-size: 24px; }
.panel-card form { margin-top: 22px; }
.demo { margin-top: 26px; border-top: 1px dashed var(--line); padding-top: 16px; }
.demo-title { font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.demo-row { display: flex; flex-direction: column; gap: 6px; }
.demo-chip {
  text-align: left; border: 1px solid var(--line); background: #fff; border-radius: 8px;
  padding: 7px 10px; font-size: 12px; color: var(--muted); cursor: pointer;
}
.demo-chip:hover { border-color: var(--primary); color: var(--primary); }
.demo-chip.admin { color: #6c5ce7; }
@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; margin: 0; }
  .hero { padding: 44px 28px; }
  .hero h1 { font-size: 32px; }
  .panel { padding: 32px 24px; }
}
</style>

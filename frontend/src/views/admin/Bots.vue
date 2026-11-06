<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { api, timeAgo } from '../../api'
import { notify } from '../../store'

const form = reactive({
  name: '刷屏行动',
  target_post_id: null,
  bot_count: 20,
  actions: ['like', 'comment'],
  comment_text: '支持一下，顶起来',
  interval_ms: 400,
  duration_s: 30
})
const posts = ref([])
const campaigns = ref([])
const stats = ref(null)
const creating = ref(false)
const detail = ref(null)
const detailOpen = ref(false)
const chartEl = ref(null)
let chart = null
let timer = null

async function load() {
  try {
    const [c, s] = await Promise.all([api.get('/admin/campaigns'), api.get('/admin/stats')])
    campaigns.value = c
    stats.value = s
    if (detailOpen.value && detail.value) {
      const d = await api.get(`/admin/campaigns/${detail.value.id}`)
      detail.value = d
      renderChart()
    }
  } catch (e) {
    console.error(e)
  }
}

async function loadPosts() {
  const data = await api.get('/posts?size=50&sort=latest')
  posts.value = data.items
  if (!form.target_post_id && posts.value.length) form.target_post_id = posts.value[0].id
}

function toggleAction(a) {
  const idx = form.actions.indexOf(a)
  if (idx >= 0) form.actions.splice(idx, 1)
  else form.actions.push(a)
}

async function createCampaign() {
  if (!form.actions.length) { notify('至少选择一种动作', 'error'); return }
  creating.value = true
  try {
    const res = await api.post('/admin/campaigns', {
      ...form,
      actions: form.actions.join(','),
      target_post_id: form.target_post_id || null
    })
    notify('水军任务已启动', 'success')
    await load()
    openDetail(res.id)
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    creating.value = false
  }
}

async function openDetail(id) {
  try {
    detail.value = await api.get(`/admin/campaigns/${id}`)
    detailOpen.value = true
    await nextTick()
    renderChart()
  } catch (e) { notify(e.message, 'error') }
}

function renderChart() {
  if (!chartEl.value || !detail.value) return
  chart = chart || echarts.init(chartEl.value)
  const series = detail.value.series || []
  chart.setOption({
    grid: { left: 38, right: 12, top: 16, bottom: 26 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: series.map((p) => `${p.t}s`), axisLabel: { fontSize: 10, color: '#7a8194' } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#7a8194' }, splitLine: { lineStyle: { color: '#f0f1f6' } } },
    series: [{
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 5,
      data: series.map((p) => p.count),
      lineStyle: { width: 3, color: '#6c5ce7' },
      itemStyle: { color: '#6c5ce7' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(108,92,231,.35)' },
          { offset: 1, color: 'rgba(108,92,231,0)' }
        ])
      }
    }]
  })
}

async function stopCampaign(id) {
  try {
    await api.post(`/admin/campaigns/${id}/stop`)
    notify('任务已停止', 'success')
    await load()
    if (detail.value?.id === id) openDetail(id)
  } catch (e) { notify(e.message, 'error') }
}

function closeDetail() {
  detailOpen.value = false
  chart?.dispose()
  chart = null
}

onMounted(async () => {
  await loadPosts()
  await load()
  timer = setInterval(load, 2500)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  chart?.dispose()
})
</script>

<template>
  <div class="stack">
    <header class="row-between">
      <div>
        <h1>水军模拟</h1>
        <p class="muted small" style="margin: 4px 0 0">
          在沙箱内批量创建账号并模拟协同行为，用于研究刷屏与协同检测；不连接任何真实平台
        </p>
      </div>
      <span class="badge badge-bot">已创建 BOT：{{ stats?.bots ?? '-' }}</span>
    </header>

    <div class="bot-grid">
      <section class="card panel">
        <h3>新建任务</h3>
        <div class="field">
          <label>任务名称</label>
          <input v-model="form.name" class="input" maxlength="60" />
        </div>
        <div class="field">
          <label>目标帖子（刷热度对象）</label>
          <select v-model="form.target_post_id" class="input">
            <option v-for="p in posts" :key="p.id" :value="p.id">
              #{{ p.id }} · {{ (p.content || '[媒体]').slice(0, 26) }}
            </option>
          </select>
        </div>
        <div class="two">
          <div class="field">
            <label>BOT 数量</label>
            <input v-model.number="form.bot_count" type="number" min="1" max="50" class="input" />
          </div>
          <div class="field">
            <label>持续时长（秒）</label>
            <input v-model.number="form.duration_s" type="number" min="5" max="600" class="input" />
          </div>
        </div>
        <div class="field">
          <label>动作（可多选）</label>
          <div class="chips">
            <button
              v-for="a in [
                { key: 'like', label: '点赞' },
                { key: 'comment', label: '评论' },
                { key: 'follow', label: '关注' },
                { key: 'post', label: '发帖' }
              ]"
              :key="a.key"
              class="chip"
              :class="{ active: form.actions.includes(a.key) }"
              @click="toggleAction(a.key)"
            >
              {{ a.label }}
            </button>
          </div>
        </div>
        <div class="field">
          <label>评论话术</label>
          <input v-model="form.comment_text" class="input" maxlength="300" />
        </div>
        <div class="field">
          <label>动作间隔 {{ form.interval_ms }}ms</label>
          <input v-model.number="form.interval_ms" type="range" min="100" max="2000" step="50" />
        </div>
        <button class="btn btn-primary" :disabled="creating" @click="createCampaign">
          <span v-if="creating" class="spinner"></span>启动水军任务
        </button>
        <p class="muted small" style="margin: 10px 0 0">
          提示：勾选「发帖」后，BOT 会发布同音字变体广告，用来演示“基线漏过、增强防御拦截”。
        </p>
      </section>

      <section class="card panel">
        <div class="row-between">
          <h3>任务列表</h3>
          <button class="btn btn-sm" @click="load">刷新</button>
        </div>
        <div v-if="!campaigns.length" class="empty" style="padding: 30px">还没有任务</div>
        <div v-else class="campaign-list">
          <div v-for="c in campaigns" :key="c.id" class="campaign" @click="openDetail(c.id)">
            <div class="row-between">
              <div class="row" style="gap: 8px">
                <span class="badge" :class="c.status === 'running' ? 'badge-pending' : 'badge-ok'">
                  {{ c.status === 'running' ? '运行中' : c.status === 'done' ? '已完成' : c.status === 'stopped' ? '已停止' : c.status }}
                </span>
                <strong>{{ c.name }}</strong>
              </div>
              <span class="muted small">{{ timeAgo(c.created_at) }}</span>
            </div>
            <div class="muted small campaign-meta">
              {{ c.bot_count }} 个 BOT · {{ c.actions }} · 已执行 {{ c.actions_done }} 次
            </div>
            <div class="progress"><i :style="{ width: Math.min(100, c.actions_done / 1.2) + '%' }"></i></div>
          </div>
        </div>
      </section>
    </div>

    <div v-if="detailOpen && detail" class="modal-mask" @click.self="closeDetail">
      <div class="modal card">
        <div class="row-between">
          <h3>{{ detail.name }}</h3>
          <button class="btn btn-sm" @click="closeDetail">关闭</button>
        </div>
        <div class="row wrap" style="gap: 8px; margin: 8px 0 12px">
          <span class="badge" :class="detail.status === 'running' ? 'badge-pending' : 'badge-ok'">{{ detail.status }}</span>
          <span class="muted small">{{ detail.bot_count }} 个 BOT</span>
          <span class="muted small">已执行 {{ detail.actions_done }} 次</span>
          <span v-if="detail.target" class="muted small">目标：#{{ detail.target.id }}</span>
        </div>
        <div ref="chartEl" class="chart"></div>
        <div v-if="detail.status === 'running'" class="row" style="margin-top: 10px">
          <button class="btn btn-danger btn-sm" @click="stopCampaign(detail.id)">停止任务</button>
        </div>
        <div class="recent">
          <div class="muted small" style="margin-bottom: 6px">最近动作</div>
          <div v-for="(a, i) in detail.recent_actions" :key="i" class="action-row">
            <span class="mono">BOT #{{ a.bot_id }}</span>
            <span class="badge">{{ a.action }}</span>
            <span class="muted small">{{ a.time.slice(11, 19) }}</span>
          </div>
          <div v-if="!detail.recent_actions.length" class="muted small">暂无动作，等待调度……</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bot-grid { display: grid; grid-template-columns: 380px minmax(0, 1fr); gap: 14px; align-items: start; }
.panel { padding: 16px; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { border: 1px solid var(--line); background: #fff; border-radius: 999px; padding: 5px 12px; font-size: 12px; cursor: pointer; color: var(--muted); }
.chip.active { background: #f0edff; border-color: #c9c2ff; color: var(--primary); font-weight: 600; }
.campaign-list { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.campaign { border: 1px solid var(--line); border-radius: 12px; padding: 11px 12px; cursor: pointer; transition: all .15s; }
.campaign:hover { border-color: #c9c2ff; background: #fbfaff; }
.campaign-meta { margin-top: 4px; }
.progress { height: 5px; background: var(--bg-soft); border-radius: 99px; margin-top: 8px; overflow: hidden; }
.progress i { display: block; height: 100%; background: linear-gradient(90deg, #6c5ce7, #a29bfe); border-radius: 99px; transition: width .4s; }
.modal-mask { position: fixed; inset: 0; background: rgba(18, 20, 32, .45); display: grid; place-items: center; z-index: 60; padding: 20px; }
.modal { width: min(620px, 96vw); padding: 18px; max-height: 88vh; overflow: auto; }
.chart { height: 220px; }
.recent { margin-top: 12px; border-top: 1px solid var(--line); padding-top: 10px; max-height: 160px; overflow: auto; }
.action-row { display: flex; align-items: center; gap: 8px; font-size: 12px; padding: 3px 0; }
@media (max-width: 960px) {
  .bot-grid { grid-template-columns: 1fr; }
}
</style>

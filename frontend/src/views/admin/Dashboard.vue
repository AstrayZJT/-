<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { api, timeAgo } from '../../api'

const stats = ref(null)
const metrics = ref(null)
const pending = ref([])
const barEl = ref(null)
const pieEl = ref(null)
let barChart = null
let pieChart = null

const approved = computed(() => {
  if (!stats.value) return 0
  return Math.max(0, stats.value.posts - stats.value.pending - stats.value.rejected)
})

const cards = computed(() => [
  { label: '注册用户', value: stats.value?.users ?? '-', hint: '不含水军账号', icon: '👤', color: '#5b5bd6' },
  { label: '动态总数', value: stats.value?.posts ?? '-', hint: '图文与视频', icon: '📝', color: '#0984e3' },
  { label: '待审核', value: stats.value?.pending ?? '-', hint: '需要人工复核', icon: '⏳', color: '#e17055' },
  { label: 'BOT 账号', value: stats.value?.bots ?? '-', hint: '水军模拟用', icon: '🤖', color: '#00b894' }
])

function renderBar() {
  if (!barEl.value) return
  barChart = barChart || echarts.init(barEl.value)
  const evasion = metrics.value?.text_metrics?.attack_evasion || {}
  const types = Object.keys(evasion)
  barChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => `${(v * 100).toFixed(1)}%` },
    legend: { bottom: 0, textStyle: { color: '#7a8194', fontSize: 11 } },
    grid: { left: 44, right: 16, top: 24, bottom: 58 },
    xAxis: { type: 'category', data: types, axisLine: { lineStyle: { color: '#e6e8ef' } }, axisLabel: { fontSize: 11 } },
    yAxis: {
      type: 'value', max: 1,
      axisLabel: { formatter: (v) => `${Math.round(v * 100)}%`, color: '#7a8194', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f1f6' } }
    },
    series: [
      { name: '关键词基线', type: 'bar', data: types.map((t) => evasion[t].keyword_evasion), itemStyle: { color: '#ff7675', borderRadius: [4, 4, 0, 0] } },
      { name: '归一化防御', type: 'bar', data: types.map((t) => evasion[t].normalize_evasion), itemStyle: { color: '#74b9ff', borderRadius: [4, 4, 0, 0] } },
      { name: '归一化 + 模型', type: 'bar', data: types.map((t) => evasion[t].model_evasion), itemStyle: { color: '#00b894', borderRadius: [4, 4, 0, 0] } }
    ]
  })
}

function renderPie() {
  if (!pieEl.value) return
  pieChart = pieChart || echarts.init(pieEl.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#7a8194', fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['46%', '68%'],
      center: ['50%', '44%'],
      label: { show: false },
      data: [
        { name: '已通过', value: approved.value, itemStyle: { color: '#00b894' } },
        { name: '待审核', value: stats.value?.pending || 0, itemStyle: { color: '#fdcb6e' } },
        { name: '未通过', value: stats.value?.rejected || 0, itemStyle: { color: '#ff7675' } }
      ]
    }]
  })
}

async function load() {
  const [s, m, p] = await Promise.all([
    api.get('/admin/stats'),
    api.get('/admin/lab/metrics').catch(() => null),
    api.get('/admin/moderation?status=pending&limit=5').catch(() => [])
  ])
  stats.value = s
  metrics.value = m
  pending.value = p
  await nextTick()
  renderBar()
  renderPie()
}

function resize() {
  barChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  barChart?.dispose()
  pieChart?.dispose()
})
</script>

<template>
  <div class="stack">
    <header class="row-between">
      <div>
        <h1>运营概览</h1>
        <p class="muted small" style="margin: 4px 0 0">平台运行状态、内容审核与水军活动的实时汇总</p>
      </div>
      <button class="btn btn-sm" @click="load">刷新</button>
    </header>

    <div class="stat-grid">
      <div v-for="c in cards" :key="c.label" class="card stat-card">
        <div class="stat-icon" :style="{ background: c.color + '18', color: c.color }">{{ c.icon }}</div>
        <div>
          <div class="stat-value">{{ c.value }}</div>
          <div class="stat-label">{{ c.label }}</div>
          <div class="muted small">{{ c.hint }}</div>
        </div>
      </div>
    </div>

    <div class="chart-grid">
      <div class="card chart-card">
        <div class="row-between">
          <h3>文本对抗：不同防御下的绕过率</h3>
          <span class="muted small">越低越好</span>
        </div>
        <div ref="barEl" class="chart"></div>
        <p class="muted small" style="margin: 6px 0 0">
          关键词基线遇同音字即失效；归一化可拦住多数字符变体；机器学习模型兜住 Emoji 等改写。
        </p>
      </div>
      <div class="card chart-card">
        <h3>内容审核分布</h3>
        <div ref="pieEl" class="chart"></div>
        <router-link to="/admin/moderation" class="btn btn-sm" style="width: 100%">去审核队列</router-link>
      </div>
    </div>

    <div class="card panel">
      <div class="row-between">
        <h3>最新待审核</h3>
        <router-link to="/admin/moderation" class="small">查看全部 →</router-link>
      </div>
      <div v-if="!pending.length" class="empty" style="padding: 24px">队列已清空，辛苦了 🎉</div>
      <table v-else class="table">
        <thead>
          <tr><th>内容</th><th>类型</th><th>原因</th><th>时间</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in pending" :key="item.id">
            <td class="cell-text">{{ item.post.content || '[媒体内容]' }}</td>
            <td><span class="badge" :class="item.label === 'ad' ? 'badge-ad' : 'badge-abuse'">{{ item.label === 'ad' ? '广告' : '辱骂' }}</span></td>
            <td class="muted small">{{ item.reason }}</td>
            <td class="muted small">{{ timeAgo(item.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.stat-card { padding: 16px; display: flex; gap: 12px; align-items: center; }
.stat-icon { width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center; font-size: 20px; }
.stat-value { font-size: 24px; font-weight: 800; line-height: 1.1; }
.stat-label { font-size: 13px; font-weight: 600; margin-top: 2px; }
.chart-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 12px; }
.chart-card { padding: 16px; }
.chart { height: 240px; margin-top: 6px; }
.panel { padding: 16px; }
.cell-text { max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 1000px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-grid { grid-template-columns: 1fr; }
}
</style>

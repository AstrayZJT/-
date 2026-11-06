<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'
import { notify } from '../../store'

const settings = ref(null)
const selected = ref(0)
const saving = ref(false)

const levelInfo = [
  {
    level: 0,
    title: '基线：仅分类模型',
    tag: '最脆弱',
    desc: '文本只做关键词黑名单匹配，图片用干净模型，视频固定 1fps 抽帧。用于复现“没有防御时”的状态。',
    bullets: ['同音字、零宽字符可直接绕过关键词', '对抗扰动可使图片分类翻转', '违规画面落在采样间隙会被漏掉']
  },
  {
    level: 1,
    title: '归一化：字符层防御',
    tag: '入门',
    desc: '关键词匹配前先做字符归一化：全半角、零宽字符、同音字、分隔符统一还原。',
    bullets: ['拦住同音字、零宽、拆分等字符变体', '图片对抗样本仍然有效', '视频抽帧间隙仍然存在']
  },
  {
    level: 2,
    title: '增强：对抗训练 + 密采样',
    tag: '推荐',
    desc: '文本归一化后交给分类模型；图片换成对抗训练 CNN；视频改为 0.4s 密采样并随机相位。',
    bullets: ['模型能识别 Emoji 插入等改写变体', '对抗训练显著降低图片攻击成功率', '密采样抓住 0.3s 的瞬时违规画面']
  }
]

const current = computed(() => levelInfo.find((l) => l.level === selected.value))

async function load() {
  settings.value = await api.get('/admin/settings')
  selected.value = settings.value.defense_level
}

async function save() {
  saving.value = true
  try {
    const res = await api.put('/admin/settings', { defense_level: selected.value })
    settings.value = res
    notify(`已切换到防御等级 ${res.defense_level}`, 'success')
  } catch (e) {
    notify(e.message, 'error')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="stack">
    <header>
      <h1>防御设置</h1>
      <p class="muted small" style="margin: 4px 0 0">
        切换后立即影响平台的所有审核：新发帖、BOT 发帖、视频抽帧都会按新等级执行
      </p>
    </header>

    <div class="level-grid">
      <button
        v-for="l in levelInfo"
        :key="l.level"
        class="card level-card"
        :class="{ active: selected === l.level }"
        @click="selected = l.level"
      >
        <div class="row-between">
          <span class="badge">等级 {{ l.level }}</span>
          <span class="badge" :class="l.level === 0 ? 'badge-rejected' : l.level === 1 ? 'badge-pending' : 'badge-ok'">{{ l.tag }}</span>
        </div>
        <h3>{{ l.title }}</h3>
        <p class="muted small">{{ l.desc }}</p>
      </button>
    </div>

    <div v-if="current" class="card panel">
      <h3>{{ current.title }} 的具体行为</h3>
      <ul class="bullets">
        <li v-for="b in current.bullets" :key="b">{{ b }}</li>
      </ul>
      <div class="row" style="margin-top: 14px">
        <button class="btn btn-primary" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner"></span>应用等级 {{ selected }}
        </button>
        <span class="muted small">当前生效：等级 {{ settings?.defense_level }}</span>
      </div>
    </div>

    <div class="card panel">
      <h3>各等级行为对照</h3>
      <table class="table">
        <thead><tr><th>模块</th><th>等级 0</th><th>等级 1</th><th>等级 2</th></tr></thead>
        <tbody>
          <tr><td>文本审核</td><td>关键词黑名单</td><td>归一化 + 关键词</td><td>归一化 + 分类模型</td></tr>
          <tr><td>图片审核</td><td>干净 CNN</td><td>干净 CNN</td><td>对抗训练 CNN</td></tr>
          <tr><td>视频审核</td><td>1fps 固定采样</td><td>1fps 固定采样</td><td>0.4s 密采样 + 随机相位</td></tr>
          <tr><td>适用场景</td><td>漏洞复现</td><td>日常</td><td>演示 / 对抗环境</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.level-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.level-card { padding: 16px; text-align: left; cursor: pointer; transition: all .15s; }
.level-card:hover { border-color: #c9c2ff; }
.level-card.active { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(91, 91, 214, .12); }
.level-card h3 { margin: 10px 0 6px; }
.panel { padding: 16px; }
.bullets { margin: 8px 0 0; padding-left: 18px; color: var(--muted); line-height: 2; }
@media (max-width: 900px) { .level-grid { grid-template-columns: 1fr; } }
</style>

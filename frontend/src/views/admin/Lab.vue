<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'
import { notify } from '../../store'

const tab = ref('text')
const defense = ref(null)
const text = ref('加微信 abc123 兼职日结，一天300，名额有限')
const textResult = ref(null)
const textLoading = ref(false)

const imageFile = ref(null)
const imagePreview = ref('')
const eps = ref(24)
const imageResult = ref(null)
const imageLoading = ref(false)
const imageInput = ref(null)

const videoResult = ref(null)
const videoLoading = ref(false)
const metrics = ref(null)

const presets = [
  '加微信 abc123 兼职日结，一天300',
  '专业代写课程设计，价格美丽，私聊',
  '你就是个傻X，别在这丢人现眼'
]

const levelLabel = computed(() => defense.value?.levels?.[defense.value?.defense_level] || '')

async function loadMeta() {
  try {
    defense.value = await api.get('/admin/settings')
    metrics.value = await api.get('/admin/lab/metrics')
  } catch (e) { console.error(e) }
}

async function runText() {
  if (!text.value.trim()) return
  textLoading.value = true
  try {
    textResult.value = await api.post('/admin/lab/text', { text: text.value })
  } catch (e) { notify(e.message, 'error') } finally { textLoading.value = false }
}

function pickImage() { imageInput.value?.click() }

function onImage(e) {
  const f = e.target.files?.[0]
  if (!f) return
  imageFile.value = f
  imagePreview.value = URL.createObjectURL(f)
  imageResult.value = null
  e.target.value = ''
}

async function runImage() {
  if (!imageFile.value) { notify('先选一张图片', 'error'); return }
  imageLoading.value = true
  try {
    imageResult.value = await api.uploadImage(imageFile.value, eps.value / 255)
  } catch (e) { notify(e.message, 'error') } finally { imageLoading.value = false }
}

async function runVideo() {
  videoLoading.value = true
  try {
    videoResult.value = await api.post('/admin/lab/video', { rate: 1.0 })
  } catch (e) { notify(e.message, 'error') } finally { videoLoading.value = false }
}

async function loadSample(kind) {
  const res = await fetch(`/media/demo/sample_${kind}.jpg`)
  if (!res.ok) { notify('示例图片未生成', 'error'); return }
  const blob = await res.blob()
  const f = new File([blob], `sample_${kind}.jpg`, { type: 'image/jpeg' })
  imageFile.value = f
  imagePreview.value = URL.createObjectURL(f)
  imageResult.value = null
}

function labelClass(label) {
  return label === 'ad' ? 'badge-ad' : label === 'abuse' ? 'badge-abuse' : 'badge-ok'
}

onMounted(loadMeta)
</script>

<template>
  <div class="stack">
    <header class="row-between">
      <div>
        <h1>攻防实验室</h1>
        <p class="muted small" style="margin: 4px 0 0">
          同一段内容，比较“关键词基线 / 归一化 / 模型”三种状态下的检测结果
        </p>
      </div>
      <div class="level-chip">
        当前防御等级 {{ defense?.defense_level ?? '-' }}
        <span class="muted small">{{ levelLabel }}</span>
        <router-link to="/admin/settings" class="small">调整 →</router-link>
      </div>
    </header>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'text' }" @click="tab = 'text'">文本对抗</button>
      <button class="tab" :class="{ active: tab === 'image' }" @click="tab = 'image'">图片对抗</button>
      <button class="tab" :class="{ active: tab === 'video' }" @click="tab = 'video'">视频抽帧</button>
      <button class="tab" :class="{ active: tab === 'metrics' }" @click="tab = 'metrics'">实验指标</button>
    </div>

    <!-- 文本 -->
    <section v-if="tab === 'text'" class="stack">
      <div class="card panel">
        <div class="row wrap" style="gap: 6px; margin-bottom: 10px">
          <span class="muted small">示例：</span>
          <button v-for="p in presets" :key="p" class="chip" @click="text = p">{{ p.slice(0, 14) }}…</button>
        </div>
        <textarea v-model="text" class="textarea" rows="3"></textarea>
        <div class="row" style="margin-top: 10px">
          <button class="btn btn-primary" :disabled="textLoading" @click="runText">
            <span v-if="textLoading" class="spinner"></span>运行攻防对比
          </button>
          <span class="muted small">变体由同音字、零宽字符、拆分、Emoji 四类规则生成</span>
        </div>
      </div>

      <div v-if="textResult" class="stack">
        <div class="three">
          <div v-for="col in [
            { key: 'raw', title: '关键词基线', sub: '不做归一化，黑名单直匹配', tone: 'bad' },
            { key: 'normalized', title: '归一化 + 关键词', sub: '同音字/零宽/分隔符还原', tone: 'mid' },
            { key: 'robust', title: '归一化 + 模型', sub: '分类模型兜底改写变体', tone: 'good' }
          ]" :key="col.key" class="card result-card" :class="col.tone">
            <div class="muted small">{{ col.sub }}</div>
            <h3>{{ col.title }}</h3>
            <div class="verdict">
              <span class="badge" :class="labelClass(textResult[col.key].label)">
                {{ textResult[col.key].label_zh }}
              </span>
              <span class="score">{{ (textResult[col.key].score * 100).toFixed(1) }}%</span>
            </div>
            <div class="muted small">对原始文本的判断</div>
          </div>
        </div>

        <div class="card panel">
          <div class="row-between">
            <h3>对抗变体逐条结果</h3>
            <span class="muted small">“绕过”= 被判成正常</span>
          </div>
          <table class="table">
            <thead>
              <tr><th>类型</th><th>变体文本</th><th>关键词</th><th>归一化</th><th>模型</th><th>结论</th></tr>
            </thead>
            <tbody>
              <tr v-for="(v, i) in textResult.variants" :key="i">
                <td><span class="badge">{{ v.type }}</span></td>
                <td class="mono variant-text">{{ v.text }}</td>
                <td><span class="badge" :class="labelClass(v.raw.label)">{{ v.raw.label_zh }}</span></td>
                <td><span class="badge" :class="labelClass(v.normalized.label)">{{ v.normalized.label_zh }}</span></td>
                <td><span class="badge" :class="labelClass(v.robust.label)">{{ v.robust.label_zh }}</span></td>
                <td>
                  <span v-if="v.evaded" class="badge badge-rejected">基线可绕过</span>
                  <span v-else class="badge badge-ok">基线已拦截</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 图片 -->
    <section v-if="tab === 'image'" class="stack">
      <div class="card panel">
        <div class="row wrap" style="gap: 14px; align-items: flex-start">
          <div class="upload-box" @click="pickImage">
            <img v-if="imagePreview" :src="imagePreview" alt="待测图片" />
            <div v-else class="upload-placeholder">点击选择图片<br /><span class="muted small">建议用广告图 / 二维码图</span></div>
          </div>
          <div class="grow">
            <div class="row wrap" style="gap: 6px; margin-bottom: 8px">
              <span class="muted small">示例：</span>
              <button class="chip" @click="loadSample('ad')">广告图</button>
              <button class="chip" @click="loadSample('normal')">正常图</button>
            </div>
            <div class="field">
              <label>扰动预算 ε = {{ eps }}/255（约 {{ (eps / 255 * 100).toFixed(1) }}%）</label>
              <input v-model.number="eps" type="range" min="8" max="48" step="1" />
            </div>
            <p class="muted small">
              PGD 迭代 20 步，沿“使分类器判为正常”的方向累积扰动。ε 越大越容易绕过，但肉眼也能看出噪点。
            </p>
            <button class="btn btn-primary" :disabled="imageLoading" @click="runImage">
              <span v-if="imageLoading" class="spinner"></span>生成对抗样本并对比
            </button>
          </div>
        </div>
        <input ref="imageInput" type="file" accept="image/*" class="hidden" @change="onImage" />
      </div>

      <div v-if="imageResult" class="stack">
        <div class="two-img">
          <div class="card result-card">
            <div class="muted small">原始图片</div>
            <img :src="imageResult.orig_url" class="adv-img" alt="" />
            <div class="row" style="gap: 8px; margin-top: 8px">
              <span class="badge" :class="labelClass(imageResult.before.label)">{{ imageResult.before.label === 'ad' ? '广告导流' : '正常' }}</span>
              <span class="score">{{ (imageResult.before.score * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div class="card result-card">
            <div class="muted small">对抗样本（ε=24/255，有可见噪点）</div>
            <img :src="imageResult.adv_url" class="adv-img" alt="" />
            <div class="row" style="gap: 8px; margin-top: 8px">
              <span class="badge" :class="labelClass(imageResult.after.label)">{{ imageResult.after.label === 'ad' ? '广告导流' : '正常' }}</span>
              <span class="score">{{ (imageResult.after.score * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
        <div class="card panel">
          <div class="kv">
            <dt>干净模型判断</dt><dd>{{ imageResult.before.label === 'ad' ? '广告导流' : '正常' }} → {{ imageResult.after.label === 'ad' ? '广告导流' : '正常' }}</dd>
            <dt>对抗训练模型</dt><dd>{{ imageResult.robust.label === 'ad' ? '广告导流' : '正常' }}（{{ (imageResult.robust.score * 100).toFixed(1) }}%）</dd>
            <dt>扰动预算</dt><dd>ε = {{ (imageResult.eps * 255).toFixed(0) }}/255</dd>
          </div>
        </div>
      </div>
    </section>

    <!-- 视频 -->
    <section v-if="tab === 'video'" class="stack">
      <div class="card panel">
        <p class="muted" style="margin-top: 0">
          演示视频里，广告画面只出现 0.3 秒（4.65s–4.95s）。固定 1fps 抽帧会整段跳过；0.4s 密采样 + 随机相位才能稳定抓到。
        </p>
        <div class="row wrap">
          <button class="btn btn-primary" :disabled="videoLoading" @click="runVideo">
            <span v-if="videoLoading" class="spinner"></span>分析演示视频
          </button>
          <span class="muted small">视频：ad_gap.mp4（违规画面落在采样间隙）</span>
        </div>
      </div>

      <div v-if="videoResult" class="stack">
        <div class="two-img">
          <div class="card result-card bad">
            <h3>固定 1fps</h3>
            <div class="verdict">
              <span class="badge" :class="videoResult.fixed_detected ? 'badge-ok' : 'badge-rejected'">
                {{ videoResult.fixed_detected ? '检出' : '漏过' }}
              </span>
            </div>
            <div class="samples">
              <span v-for="s in videoResult.fixed.samples" :key="s.t" class="sample" :class="{ hit: s.label === 'ad' }">
                {{ s.t }}s
              </span>
            </div>
            <div class="muted small">采样点：{{ videoResult.fixed.samples.length }} 帧</div>
          </div>
          <div class="card result-card good">
            <h3>0.4s 密采样</h3>
            <div class="verdict">
              <span class="badge" :class="videoResult.dense_detected ? 'badge-ok' : 'badge-rejected'">
                {{ videoResult.dense_detected ? '检出' : '漏过' }}
              </span>
            </div>
            <div class="samples">
              <span v-for="s in videoResult.dense.samples" :key="s.t" class="sample" :class="{ hit: s.label === 'ad' }">
                {{ s.t }}s
              </span>
            </div>
            <div class="muted small">采样点：{{ videoResult.dense.samples.length }} 帧</div>
          </div>
        </div>
        <div v-if="videoResult.dense.violations.length" class="card panel">
          <h3>违规区间</h3>
          <div v-for="(v, i) in videoResult.dense.violations" :key="i" class="muted">
            第 {{ v.start }}s – {{ v.end }}s，置信度 {{ (v.score * 100).toFixed(1) }}%
          </div>
        </div>
      </div>
    </section>

    <!-- 指标 -->
    <section v-if="tab === 'metrics'" class="stack">
      <div v-if="!metrics" class="empty card">指标尚未生成，请先运行训练脚本</div>
      <template v-else>
        <div class="metric-grid">
          <div class="card metric">
            <div class="muted small">文本 · 模型准确率</div>
            <div class="metric-value">{{ metrics.text_metrics ? (metrics.text_metrics.clean_accuracy * 100).toFixed(1) + '%' : '-' }}</div>
          </div>
          <div class="card metric">
            <div class="muted small">文本 · 对抗训练后准确率</div>
            <div class="metric-value">{{ metrics.text_metrics ? (metrics.text_metrics.robust_accuracy * 100).toFixed(1) + '%' : '-' }}</div>
          </div>
          <div class="card metric">
            <div class="muted small">图片 · 干净准确率</div>
            <div class="metric-value">{{ metrics.image_metrics ? (metrics.image_metrics.clean_accuracy * 100).toFixed(1) + '%' : '-' }}</div>
          </div>
          <div class="card metric">
            <div class="muted small">图片 · PGD 攻击成功率</div>
            <div class="metric-value">{{ metrics.image_metrics ? (metrics.image_metrics.attack_success_rate * 100).toFixed(1) + '%' : '-' }}</div>
          </div>
        </div>

        <div v-if="metrics.text_metrics" class="card panel">
          <h3>文本攻击绕过率</h3>
          <table class="table">
            <thead><tr><th>变体类型</th><th>样本数</th><th>关键词基线</th><th>归一化</th><th>归一化 + 模型</th></tr></thead>
            <tbody>
              <tr v-for="(v, k) in metrics.text_metrics.attack_evasion" :key="k">
                <td>{{ k }}</td>
                <td>{{ v.samples }}</td>
                <td>{{ (v.keyword_evasion * 100).toFixed(1) }}%</td>
                <td>{{ (v.normalize_evasion * 100).toFixed(1) }}%</td>
                <td>{{ (v.model_evasion * 100).toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="metrics.video_metrics" class="card panel">
          <h3>视频抽帧策略</h3>
          <div class="kv">
            <dt>1fps 漏检演示</dt><dd>{{ metrics.video_metrics.fixed_1fps.ad_gap_detected ? '检出' : '漏过' }}</dd>
            <dt>1fps 命中对照</dt><dd>{{ metrics.video_metrics.fixed_1fps.ad_hit_detected ? '检出' : '漏过' }}</dd>
            <dt>0.4s 密采样</dt><dd>检出率 {{ (metrics.video_metrics.dense_0_4s.ad_gap_detection_rate * 100).toFixed(1) }}%</dd>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.panel { padding: 16px; }
.chip { border: 1px solid var(--line); background: #fff; border-radius: 999px; padding: 4px 10px; font-size: 12px; cursor: pointer; color: var(--muted); }
.chip:hover { border-color: var(--primary); color: var(--primary); }
.level-chip { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; font-size: 12px; }
.three { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.two-img { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.result-card { padding: 14px; border-top: 4px solid var(--line); }
.result-card.bad { border-top-color: #ff7675; }
.result-card.mid { border-top-color: #74b9ff; }
.result-card.good { border-top-color: #00b894; }
.result-card h3 { margin: 4px 0 10px; }
.verdict { display: flex; align-items: baseline; gap: 8px; margin: 6px 0; }
.score { font-size: 22px; font-weight: 800; }
.variant-text { max-width: 320px; word-break: break-all; font-size: 12px; }
.upload-box {
  width: 190px; height: 150px; border: 2px dashed var(--line); border-radius: 12px;
  display: grid; place-items: center; cursor: pointer; overflow: hidden; background: var(--bg-soft);
}
.upload-box img { width: 100%; height: 100%; object-fit: cover; }
.upload-placeholder { text-align: center; font-size: 13px; color: var(--muted); line-height: 1.8; }
.adv-img { width: 100%; border-radius: 10px; display: block; background: var(--bg-soft); }
.samples { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }
.sample { font-size: 10px; padding: 2px 5px; border-radius: 4px; background: var(--bg-soft); color: var(--muted); }
.sample.hit { background: #ff7675; color: #fff; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.metric { padding: 14px; }
.metric-value { font-size: 24px; font-weight: 800; margin-top: 4px; }
@media (max-width: 900px) {
  .three, .two-img, .metric-grid { grid-template-columns: 1fr; }
}
</style>

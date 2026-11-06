<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: '' },
  size: { type: Number, default: 40 },
  bot: { type: Boolean, default: false }
})

const palettes = [
  ['#6c5ce7', '#a29bfe'],
  ['#e17055', '#fab1a0'],
  ['#00b894', '#55efc4'],
  ['#0984e3', '#74b9ff'],
  ['#d63031', '#ff7675'],
  ['#fdcb6e', '#ffeaa7']
]
const colors = computed(() => {
  let h = 0
  for (const ch of props.name) h = (h * 31 + ch.charCodeAt(0)) % 997
  return palettes[h % palettes.length]
})
const initial = computed(() => (props.name || '?').slice(0, 1))
</script>

<template>
  <div
    class="avatar"
    :class="{ bot }"
    :style="{
      width: size + 'px',
      height: size + 'px',
      fontSize: size * 0.42 + 'px',
      background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`
    }"
  >
    {{ initial }}
    <span v-if="bot" class="bot-mark">BOT</span>
  </div>
</template>

<style scoped>
.avatar {
  position: relative;
  border-radius: 50%;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex: none;
  user-select: none;
}
.bot-mark {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  background: #2d3436;
  color: #fff;
  border-radius: 4px;
  padding: 0 3px;
  letter-spacing: .5px;
}
</style>

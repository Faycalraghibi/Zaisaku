<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  Mic,
  AlertTriangle,
  Sparkles,
  User,
  Clock,
  Gauge,
  SkipForward,
  CheckCircle2,
  FileAudio
} from 'lucide-vue-next'

const props = defineProps({
  ticker: {
    type: String,
    default: 'NVDA'
  },
  companyName: {
    type: String,
    default: 'NVIDIA Corporation'
  }
})

const loading = ref(false)
const error = ref(null)
const sessionData = ref(null)

const isPlaying = ref(false)
const currentTime = ref(0)
const playbackSpeed = ref(1.0)
const canvasRef = ref(null)
let animationFrameId = null
let lastTimestamp = null

// Speed options
const speeds = [1.0, 1.25, 1.5, 2.0]

const totalDuration = computed(() => {
  return sessionData.value?.total_duration_seconds || 145.0
})

const currentUtteranceIndex = computed(() => {
  if (!sessionData.value || !sessionData.value.utterances) return -1
  const t = currentTime.value
  return sessionData.value.utterances.findIndex(u => {
    return t >= u.timestamp_seconds && t < (u.timestamp_seconds + u.duration_seconds)
  })
})

const currentUtterance = computed(() => {
  const idx = currentUtteranceIndex.value
  if (idx === -1 && sessionData.value?.utterances?.length) {
    // If before first utterance, return first; if after last, return last
    if (currentTime.value < sessionData.value.utterances[0].timestamp_seconds) {
      return sessionData.value.utterances[0]
    }
    return sessionData.value.utterances[sessionData.value.utterances.length - 1]
  }
  return sessionData.value?.utterances[idx] || null
})

const fetchCallSession = async () => {
  pauseAudio()
  currentTime.value = 0
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/forensics/calls/${encodeURIComponent(props.ticker)}`)
    if (!res.ok) {
      throw new Error(`Failed to load earnings call session (${res.status})`)
    }
    sessionData.value = await res.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
    drawWaveform()
  }
}

watch(() => props.ticker, () => {
  fetchCallSession()
})

const formatTime = (secs) => {
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const togglePlay = () => {
  if (isPlaying.value) {
    pauseAudio()
  } else {
    playAudio()
  }
}

const playAudio = () => {
  if (currentTime.value >= totalDuration.value) {
    currentTime.value = 0
  }
  isPlaying.value = true
  lastTimestamp = performance.now()
  animationLoop()
}

const pauseAudio = () => {
  isPlaying.value = false
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  lastTimestamp = null
  drawWaveform()
}

const resetAudio = () => {
  pauseAudio()
  currentTime.value = 0
  drawWaveform()
}

const seekTo = (seconds) => {
  currentTime.value = Math.min(Math.max(0, seconds), totalDuration.value)
  drawWaveform()
}

const jumpToNextDiscrepancy = () => {
  if (!sessionData.value?.utterances) return
  const current = currentTime.value
  const nextDisc = sessionData.value.utterances.find(u => u.is_discrepancy && u.timestamp_seconds > current + 1.0)
  if (nextDisc) {
    seekTo(nextDisc.timestamp_seconds)
    if (!isPlaying.value) playAudio()
  } else {
    // Wrap to first discrepancy
    const firstDisc = sessionData.value.utterances.find(u => u.is_discrepancy)
    if (firstDisc) {
      seekTo(firstDisc.timestamp_seconds)
      if (!isPlaying.value) playAudio()
    }
  }
}

// Animation loop
const animationLoop = (now = performance.now()) => {
  if (!isPlaying.value) return

  if (lastTimestamp != null) {
    const deltaSec = ((now - lastTimestamp) / 1000.0) * playbackSpeed.value
    currentTime.value += deltaSec
    if (currentTime.value >= totalDuration.value) {
      currentTime.value = totalDuration.value
      pauseAudio()
      return
    }
  }
  lastTimestamp = now

  drawWaveform()
  animationFrameId = requestAnimationFrame(animationLoop)
}

// Canvas Waveform Drawing with High-DPI support
const drawWaveform = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  const displayWidth = rect.width || 680
  const displayHeight = rect.height || 80

  const physicalWidth = Math.floor(displayWidth * dpr)
  const physicalHeight = Math.floor(displayHeight * dpr)

  if (canvas.width !== physicalWidth || canvas.height !== physicalHeight) {
    canvas.width = physicalWidth
    canvas.height = physicalHeight
  }

  ctx.save()
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, displayWidth, displayHeight)

  const numBars = 70
  const barWidth = displayWidth / numBars - 2
  const progressRatio = currentTime.value / Math.max(totalDuration.value, 1.0)
  const activeBarIndex = Math.floor(progressRatio * numBars)

  const isDiscrepancyNow = currentUtterance.value?.is_discrepancy || false
  const timeOffset = isPlaying.value ? performance.now() * 0.005 : 0

  for (let i = 0; i < numBars; i++) {
    const x = i * (barWidth + 2)
    const normalizedPos = i / numBars

    // Generate sinusoidal organic sound wave height
    const baseVal = Math.sin(normalizedPos * Math.PI * 4 + timeOffset) * 0.3 + 0.4
    const jitter = isPlaying.value && i <= activeBarIndex ? Math.sin(i * 1.5 + timeOffset * 2) * 0.2 : 0
    const barHeightNorm = Math.min(1.0, Math.max(0.12, baseVal + jitter))
    const barHeight = barHeightNorm * (displayHeight - 16)
    const y = (displayHeight - barHeight) / 2

    // Color gradient
    if (i <= activeBarIndex) {
      if (isDiscrepancyNow) {
        ctx.fillStyle = '#f43f5e' // Rose / Contradiction
      } else {
        ctx.fillStyle = '#38bdf8' // Blue / Normal
      }
    } else {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.12)'
    }

    ctx.beginPath()
    ctx.roundRect(x, y, barWidth, barHeight, 2)
    ctx.fill()
  }

  ctx.restore()
}

const handleKeydown = (e) => {
  if (['input', 'textarea'].includes(document.activeElement?.tagName?.toLowerCase())) return
  if (e.code === 'Space') {
    e.preventDefault()
    togglePlay()
  } else if (e.code === 'ArrowRight') {
    e.preventDefault()
    seekTo(currentTime.value + 5.0)
  } else if (e.code === 'ArrowLeft') {
    e.preventDefault()
    seekTo(currentTime.value - 5.0)
  } else if (e.key === 'j' || e.key === 'J') {
    e.preventDefault()
    jumpToNextDiscrepancy()
  }
}

onMounted(() => {
  fetchCallSession()
  window.addEventListener('resize', drawWaveform)
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  window.removeEventListener('resize', drawWaveform)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="audio-call-simulator bg-[#141416]/80 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 shadow-2xl transition-all">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
          <FileAudio class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-semibold text-white tracking-tight">
              Multimodal Earnings Call Audio & Transcript
            </h3>
            <span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20">
              <Mic class="w-3 h-3" /> Acoustic AI Sync
            </span>
          </div>
          <p class="text-xs text-neutral-400 mt-0.5">
            Synchronized conference call speech waveform, tone sentiment tracking, and SEC 10-Q cross-verification
          </p>
        </div>
      </div>

      <!-- Sentiment Pill & Jump Marker -->
      <div class="flex items-center gap-2" v-if="sessionData">
        <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs">
          <Gauge class="w-3.5 h-3.5 text-neutral-400" />
          <span class="text-neutral-400">Executive Tone:</span>
          <span :class="['font-semibold', sessionData.overall_executive_sentiment >= 0.5 ? 'text-emerald-400' : 'text-amber-400']">
            {{ sessionData.overall_executive_sentiment >= 0 ? '+' : '' }}{{ Math.round(sessionData.overall_executive_sentiment * 100) }}% Bullish
          </span>
        </div>

        <button
          @click="jumpToNextDiscrepancy"
          class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 rounded-lg transition-all active:scale-[0.98]"
          title="Jump to flagged contradiction against SEC filing"
        >
          <AlertTriangle class="w-3.5 h-3.5 text-rose-400" />
          <span>Jump to Contradiction</span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="p-4 my-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-xs">
      {{ error }}
    </div>

    <!-- Audio Player Visualizer -->
    <div v-if="sessionData" class="mt-5 space-y-4">
      <!-- Waveform Canvas Card -->
      <div class="p-4 rounded-xl border border-white/10 bg-black/40 relative overflow-hidden">
        <canvas
          ref="canvasRef"
          width="680"
          height="80"
          class="w-full h-20 block cursor-pointer"
          @click="(e) => {
            const rect = e.target.getBoundingClientRect()
            const pos = (e.clientX - rect.left) / rect.width
            seekTo(pos * totalDuration)
          }"
        ></canvas>

        <!-- Current Utterance Pill Overlay -->
        <div v-if="currentUtterance" class="mt-3 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div class="flex items-center gap-2">
            <span class="font-medium text-white">{{ currentUtterance.speaker }}</span>
            <span class="px-2 py-0.5 text-xs font-medium rounded-md bg-white/10 text-neutral-300">
              {{ currentUtterance.speaker_role }}
            </span>
            <span class="text-neutral-500 font-mono tabular-nums">{{ currentUtterance.timestamp_label }}</span>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-xs text-neutral-400">Tone sentiment:</span>
            <span
              :class="[
                'font-mono tabular-nums font-medium',
                currentUtterance.sentiment_score >= 0.5 ? 'text-emerald-400' : currentUtterance.sentiment_score < 0 ? 'text-rose-400' : 'text-neutral-300'
              ]"
            >
              {{ currentUtterance.sentiment_score > 0 ? '+' : '' }}{{ Math.round(currentUtterance.sentiment_score * 100) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Controls Row -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-white/[0.02] border border-white/5 rounded-xl">
        <!-- Play / Pause / Reset -->
        <div class="flex items-center gap-3">
          <button
            @click="togglePlay"
            class="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shadow-lg transition-all active:scale-[0.95]"
          >
            <Pause v-if="isPlaying" class="w-4 h-4" />
            <Play v-else class="w-4 h-4 ml-0.5" />
          </button>

          <button
            @click="resetAudio"
            class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white flex items-center justify-center transition-all active:scale-[0.95]"
            title="Restart"
          >
            <RotateCcw class="w-3.5 h-3.5" />
          </button>

          <!-- Time Display -->
          <div class="font-mono tabular-nums text-xs text-neutral-300 pl-1">
            <span class="text-white font-medium">{{ formatTime(currentTime) }}</span>
            <span class="text-neutral-500"> / {{ formatTime(totalDuration) }}</span>
          </div>
        </div>

        <!-- Scrubber Range Bar -->
        <div class="flex-1 max-w-md mx-2">
          <input
            type="range"
            min="0"
            :max="totalDuration"
            step="0.5"
            :value="currentTime"
            @input="(e) => seekTo(Number(e.target.value))"
            class="w-full accent-blue-500 h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        <!-- Speed Selector -->
        <div class="flex items-center gap-1">
          <button
            v-for="s in speeds"
            :key="s"
            @click="playbackSpeed = s"
            :class="[
              'px-2 py-1 text-xs font-medium rounded-md transition-all',
              playbackSpeed === s ? 'bg-white/20 text-white font-semibold' : 'text-neutral-400 hover:text-neutral-200'
            ]"
          >
            {{ s }}x
          </button>
        </div>
      </div>

      <!-- Synchronized Transcript Stream -->
      <div class="space-y-3 pt-2">
        <h4 class="text-xs font-semibold text-neutral-400">
          Live synchronized transcript and SEC 10-Q cross-verification
        </h4>

        <div class="space-y-2.5 max-h-[320px] overflow-y-auto pr-2 custom-scrollbar">
          <div
            v-for="(u, idx) in sessionData.utterances"
            :key="u.id"
            :class="[
              'p-3.5 rounded-xl border transition-all text-xs',
              currentUtteranceIndex === idx
                ? 'bg-blue-500/10 border-blue-500/30 shadow-md ring-1 ring-blue-500/20'
                : 'bg-white/[0.02] border-white/5 hover:border-white/10'
            ]"
          >
            <!-- Speaker & Timestamp Header -->
            <div class="flex items-center justify-between gap-2 mb-1.5">
              <div class="flex items-center gap-2">
                <span class="font-medium text-white">{{ u.speaker }}</span>
                <span class="px-1.5 py-0.5 text-xs rounded-md font-medium bg-white/10 text-neutral-400">
                  {{ u.speaker_role }}
                </span>
              </div>

              <div class="flex items-center gap-2">
                <span
                  :class="[
                    'text-[10px] font-medium px-2 py-0.5 rounded-full',
                    u.sentiment_score >= 0.5 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : u.sentiment_score < 0 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-neutral-500/10 text-neutral-300'
                  ]"
                >
                  {{ u.sentiment_score > 0 ? '+' : '' }}{{ Math.round(u.sentiment_score * 100) }}% Tone
                </span>

                <button
                  @click="seekTo(u.timestamp_seconds); if (!isPlaying) playAudio()"
                  class="font-mono text-[11px] text-blue-400 hover:text-blue-300 bg-blue-500/5 px-1.5 py-0.5 rounded border border-blue-500/10 hover:border-blue-500/30 transition-all"
                >
                  {{ u.timestamp_label }}
                </button>
              </div>
            </div>

            <!-- Speech Text -->
            <p :class="['text-xs leading-relaxed', currentUtteranceIndex === idx ? 'text-white' : 'text-neutral-300']">
              "{{ u.text }}"
            </p>

            <!-- Discrepancy Callout Box -->
            <div
              v-if="u.is_discrepancy"
              class="mt-2.5 p-2.5 bg-rose-500/10 border border-rose-500/25 rounded-lg text-rose-200 text-[11px] flex items-start gap-2"
            >
              <AlertTriangle class="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span class="font-semibold text-rose-300">SEC 10-Q Tone Contradiction Flag:</span>
                <p class="mt-0.5 text-rose-200/90 leading-normal">{{ u.discrepancy_explanation }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media (prefers-reduced-motion: reduce) {
  .audio-call-simulator,
  .audio-call-simulator * {
    transition: none !important;
    animation: none !important;
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>

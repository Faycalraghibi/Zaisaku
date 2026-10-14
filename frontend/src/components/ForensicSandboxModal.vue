<script setup>
import { ref, reactive, computed } from 'vue'
import {
  X,
  Play,
  Sparkles,
  Zap,
  Gauge,
  DollarSign,
  Cpu,
  Layers,
  FileCheck2,
  AlertCircle,
  Clock,
  CheckCircle2,
  Sliders,
  ChevronDown,
  ChevronUp
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: Boolean,
  ticker: {
    type: String,
    default: 'NVDA'
  }
})

const emit = defineEmits(['close'])

const models = [
  { id: 'llama3.3-70b-instruct', name: 'Llama 3.3 70B Instruct', provider: 'Meta AI / Local', costHint: '$0.40 / 1M' },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', costHint: '$3.00 / 1M' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', costHint: '$2.50 / 1M' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', costHint: '$0.15 / 1M' },
  { id: 'mistral-large', name: 'Mistral Large 2', provider: 'Mistral AI', costHint: '$2.00 / 1M' },
  { id: 'qwen-2.5-coder-32b', name: 'Qwen 2.5 Coder 32B', provider: 'Alibaba', costHint: '$0.35 / 1M' }
]

const promptPresets = [
  { label: 'Revenue Recognition & Contract Commitments', prompt: 'Analyze revenue recognition policies, unbilled contract commitments, and customer concentration.' },
  { label: 'Operating Margin Sustainability', prompt: 'Evaluate gross margin pricing leverage, wafer supply cost inflation, and structural operating margins.' },
  { label: 'Off-Balance-Sheet & Contingent Liabilities', prompt: 'Audit undisclosed purchase obligations, operating leases, and legal contingencies.' },
  { label: 'Cash Flow vs Net Income Divergence', prompt: 'Examine accrual quality (TATA) and divergence between GAAP operating cash flow and reported net income.' }
]

const form = reactive({
  model: 'llama3.3-70b-instruct',
  prompt: 'Analyze revenue recognition policies, unbilled contract commitments, and customer concentration.',
  systemPrompt: 'You are a Wall Street forensic equity analyst specializing in SEC disclosures and GAAP compliance.',
  temperature: 0.2,
  useRag: true
})

const showSystemPrompt = ref(false)
const loading = ref(false)
const error = ref(null)
const benchmarkResult = ref(null)

const runBenchmark = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('/api/forensics/sandbox/benchmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: form.prompt,
        system_prompt: form.systemPrompt,
        model: form.model,
        temperature: form.temperature,
        ticker: props.ticker,
        use_rag: form.useRag
      })
    })

    if (!res.ok) {
      throw new Error(`Benchmark failed with status ${res.status}`)
    }

    benchmarkResult.value = await res.json()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const applyPreset = (preset) => {
  form.prompt = preset.prompt
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn"
    @click.self="emit('close')"
  >
    <div class="relative w-full max-w-5xl max-h-[90vh] flex flex-col bg-[#141416] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
      <!-- Modal Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02]">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Cpu class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-base font-semibold text-white tracking-tight flex items-center gap-2">
              AI Prompt & RAG Laboratory Sandbox
              <span class="text-[11px] font-normal px-2 py-0.5 rounded-full bg-white/10 text-neutral-300">
                Institutional Benchmark
              </span>
            </h2>
            <p class="text-xs text-neutral-400 mt-0.5">
              Live inference latency, token efficiency, hallucination auditing, and model cost comparison
            </p>
          </div>
        </div>

        <button
          @click="emit('close')"
          class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white flex items-center justify-center transition-all"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 custom-scrollbar">
        <!-- Left: Configuration Form (5 cols) -->
        <div class="lg:col-span-5 space-y-4">
          <!-- Model Architecture -->
          <div>
            <label class="block text-xs font-semibold text-neutral-300 mb-1.5">Frontier Model Architecture</label>
            <select
              v-model="form.model"
              class="w-full bg-[#1c1c1e] border border-white/15 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 transition-all"
            >
              <option v-for="m in models" :key="m.id" :value="m.id">
                {{ m.name }} ({{ m.provider }}) — {{ m.costHint }}
              </option>
            </select>
          </div>

          <!-- Presets -->
          <div>
            <label class="block text-xs font-semibold text-neutral-300 mb-1.5">Forensic Presets</label>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="p in promptPresets"
                :key="p.label"
                type="button"
                @click="applyPreset(p)"
                class="px-2.5 py-1 text-[11px] rounded-lg bg-white/5 hover:bg-white/10 text-neutral-300 hover:text-white border border-white/10 transition-all text-left"
              >
                {{ p.label }}
              </button>
            </div>
          </div>

          <!-- User Prompt Input -->
          <div>
            <label class="block text-xs font-semibold text-neutral-300 mb-1.5">Forensic Prompt</label>
            <textarea
              v-model="form.prompt"
              rows="3"
              class="w-full bg-[#1c1c1e] border border-white/15 rounded-xl p-3 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-indigo-500 transition-all resize-none"
              placeholder="Enter forensic query or regulatory question..."
            ></textarea>
          </div>

          <!-- Collapsible System Prompt -->
          <div>
            <button
              type="button"
              @click="showSystemPrompt = !showSystemPrompt"
              class="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-neutral-200 transition-colors"
            >
              <component :is="showSystemPrompt ? ChevronUp : ChevronDown" class="w-3.5 h-3.5" />
              <span>{{ showSystemPrompt ? 'Hide System Prompt' : 'Custom System Prompt & Persona' }}</span>
            </button>
            <textarea
              v-if="showSystemPrompt"
              v-model="form.systemPrompt"
              rows="2"
              class="mt-2 w-full bg-[#1c1c1e] border border-white/10 rounded-xl p-2.5 text-[11px] text-neutral-300 focus:outline-none focus:border-indigo-500 transition-all resize-none"
            ></textarea>
          </div>

          <!-- Sliders & Toggles -->
          <div class="space-y-3 pt-2 border-t border-white/10 text-xs">
            <!-- Temperature -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <span class="text-neutral-400 font-medium">Temperature: {{ form.temperature }}</span>
                <span class="text-[10px] text-neutral-500 font-mono">
                  {{ form.temperature < 0.3 ? 'Deterministic Audit' : form.temperature < 0.7 ? 'Balanced' : 'High Variance' }}
                </span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                v-model.number="form.temperature"
                class="w-full accent-indigo-500 h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <!-- RAG Toggle -->
            <label class="flex items-center gap-2 cursor-pointer pt-1">
              <input
                type="checkbox"
                v-model="form.useRag"
                class="w-4 h-4 rounded bg-[#1c1c1e] border-white/20 text-indigo-600 focus:ring-0"
              />
              <span class="text-neutral-300">RAG Augmented Context (Inject SEC 10-K Chunks)</span>
            </label>
          </div>

          <!-- Execute Button -->
          <button
            @click="runBenchmark"
            :disabled="loading || !form.prompt.trim()"
            class="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg transition-all active:scale-[0.98]"
          >
            <Play v-if="!loading" class="w-3.5 h-3.5" />
            <span v-if="loading" class="animate-spin">⏳</span>
            <span>{{ loading ? 'Benchmarking Inference...' : 'Run Benchmark' }}</span>
          </button>
        </div>

        <!-- Right: Results & Latency Analytics (7 cols) -->
        <div class="lg:col-span-7 flex flex-col space-y-4">
          <!-- Error banner -->
          <div v-if="error" class="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-xs">
            {{ error }}
          </div>

          <!-- Placeholder if no result -->
          <div
            v-if="!benchmarkResult && !loading"
            class="flex-1 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl p-8 text-center text-neutral-500"
          >
            <Sparkles class="w-8 h-8 text-neutral-600 mb-2" />
            <p class="text-xs">Select a model, adjust parameters, and click "Run Benchmark" to test latency and token metrics.</p>
          </div>

          <!-- Loading skeleton -->
          <div v-else-if="loading" class="flex-1 flex flex-col items-center justify-center p-8 text-neutral-400 gap-3">
            <Cpu class="w-7 h-7 text-indigo-400 animate-pulse" />
            <span class="text-xs">Computing forward inference pass, evaluating groundedness and token pricing...</span>
          </div>

          <!-- Benchmark Metrics Cards -->
          <div v-else-if="benchmarkResult" class="space-y-4">
            <!-- 4 Grid KPIs -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div class="p-3 rounded-xl bg-white/[0.03] border border-white/10">
                <div class="flex items-center gap-1.5 text-neutral-400 text-[11px] mb-1">
                  <Clock class="w-3.5 h-3.5 text-blue-400" />
                  <span>Latency</span>
                </div>
                <div class="text-base font-semibold text-white font-mono">
                  {{ benchmarkResult.latency_ms }} ms
                </div>
              </div>

              <div class="p-3 rounded-xl bg-white/[0.03] border border-white/10">
                <div class="flex items-center gap-1.5 text-neutral-400 text-[11px] mb-1">
                  <Zap class="w-3.5 h-3.5 text-amber-400" />
                  <span>Speed</span>
                </div>
                <div class="text-base font-semibold text-white font-mono">
                  {{ benchmarkResult.tokens_per_second }} t/s
                </div>
              </div>

              <div class="p-3 rounded-xl bg-white/[0.03] border border-white/10">
                <div class="flex items-center gap-1.5 text-neutral-400 text-[11px] mb-1">
                  <Layers class="w-3.5 h-3.5 text-emerald-400" />
                  <span>Tokens</span>
                </div>
                <div class="text-base font-semibold text-white font-mono">
                  {{ benchmarkResult.total_tokens }}
                </div>
                <div class="text-[10px] text-neutral-500">
                  {{ benchmarkResult.input_tokens }} in / {{ benchmarkResult.output_tokens }} out
                </div>
              </div>

              <div class="p-3 rounded-xl bg-white/[0.03] border border-white/10">
                <div class="flex items-center gap-1.5 text-neutral-400 text-[11px] mb-1">
                  <DollarSign class="w-3.5 h-3.5 text-violet-400" />
                  <span>Est. Cost</span>
                </div>
                <div class="text-base font-semibold text-emerald-400 font-mono">
                  ${{ benchmarkResult.estimated_cost_usd }}
                </div>
              </div>
            </div>

            <!-- Factual Evaluation Row -->
            <div class="p-3.5 rounded-xl bg-white/[0.02] border border-white/10 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div class="flex items-center gap-2">
                <span class="text-neutral-400">Groundedness:</span>
                <span class="font-bold text-white">
                  {{ Math.round(benchmarkResult.eval_metrics.groundedness_score * 100) }}%
                </span>
              </div>

              <div class="flex items-center gap-2">
                <span class="text-neutral-400">Hallucination Risk:</span>
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-[10px] font-semibold',
                    benchmarkResult.eval_metrics.hallucination_risk === 'LOW'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  ]"
                >
                  {{ benchmarkResult.eval_metrics.hallucination_risk }}
                </span>
              </div>

              <div class="flex items-center gap-2">
                <span class="text-neutral-400">Factual Density:</span>
                <span class="font-bold text-blue-400">
                  {{ Math.round(benchmarkResult.eval_metrics.factual_density * 100) }}%
                </span>
              </div>
            </div>

            <!-- Generated Output Container -->
            <div class="p-4 rounded-xl bg-black/40 border border-white/10 text-xs text-neutral-200 leading-relaxed max-h-[220px] overflow-y-auto custom-scrollbar">
              <div class="whitespace-pre-wrap font-sans text-xs">
                {{ benchmarkResult.generated_response }}
              </div>
            </div>

            <!-- Retrieved RAG Chunks (if any) -->
            <div v-if="benchmarkResult.retrieval_chunks?.length" class="space-y-2">
              <div class="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <FileCheck2 class="w-3.5 h-3.5 text-indigo-400" />
                <span>Vector Ingested Chunks (Cosine Sim)</span>
              </div>
              <div class="space-y-1.5">
                <div
                  v-for="chunk in benchmarkResult.retrieval_chunks"
                  :key="chunk.id"
                  class="p-2.5 rounded-lg bg-white/[0.02] border border-white/5 text-[11px] text-neutral-300"
                >
                  <div class="flex items-center justify-between text-neutral-400 mb-1">
                    <span class="font-medium text-white">{{ chunk.source }}</span>
                    <span class="font-mono text-indigo-400">{{ (chunk.score * 100).toFixed(1) }}% match</span>
                  </div>
                  <p class="text-neutral-400 line-clamp-2">{{ chunk.content }}</p>
                </div>
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
  .animate-fadeIn {
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
</style>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  Cpu,
  Layers,
  Database,
  ShieldCheck,
  Zap,
  Code2,
  Workflow,
  X,
  ExternalLink,
  CheckCircle2,
  GitBranch
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const handleKeyDown = (e) => {
  if (e.key === 'Escape' && props.isOpen) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <div 
      v-if="isOpen" 
      class="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
      @click="emit('close')"
    ></div>

    <!-- Drawer with Apple Spring physics -->
    <Transition name="spring-drawer">
      <div 
        v-if="isOpen"
        class="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-slate-900/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl flex flex-col text-slate-100 overflow-hidden"
        role="dialog"
        aria-modal="true"
      >
        <!-- Header -->
        <div class="h-16 px-6 border-b border-white/10 flex items-center justify-between shrink-0 bg-slate-900/60 backdrop-blur-md">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Code2 class="w-5 h-5" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-white flex items-center gap-2">
                System Architecture & Tech Stack
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Production RAG
                </span>
              </h3>
              <p class="text-[11px] text-slate-400">Enterprise engineering blueprint and architecture specifications</p>
            </div>
          </div>

          <button 
            @click="emit('close')"
            class="apple-press p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Scrollable Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          
          <!-- Value Statement for Clients -->
          <div class="p-4 rounded-2xl bg-gradient-to-br from-emerald-950/30 to-teal-950/30 border border-emerald-500/30 space-y-2">
            <h4 class="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
              <Zap class="w-4 h-4 text-emerald-400" />
              Why this architecture proves senior engineering capability:
            </h4>
            <p class="text-xs text-slate-200 leading-relaxed">
              This platform isn't a simple LLM wrapper. It is an end-to-end, multi-tier financial intelligence pipeline that integrates sliding-window ingestion, vector search with cross-encoder re-ranking, multi-factor probabilistic forensic models, and streaming Server-Sent Events (SSE).
            </p>
          </div>

          <!-- Architecture Pillars Grid -->
          <div class="space-y-4">
            <h4 class="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold">
              Core Technical Components
            </h4>

            <!-- Pillar 1: Ingestion & Vector Search -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
              <div class="flex items-center gap-2 text-white font-semibold text-xs">
                <Database class="w-4 h-4 text-sky-400" />
                <span>1. Ingestion, Chunking & ChromaDB Vector Store</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed">
                Sliding window token chunker (512 tokens / 128 overlap) handles large multi-hundred-page 10-K and 10-Q filings with sentence-boundary preservation. Embeddings computed via <code class="text-sky-300">all-MiniLM-L6-v2</code> and indexed in ChromaDB.
              </p>
            </div>

            <!-- Pillar 2: Cross-Encoder Reranking -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
              <div class="flex items-center gap-2 text-white font-semibold text-xs">
                <Layers class="w-4 h-4 text-purple-400" />
                <span>2. Cross-Encoder Semantic Reranker</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed">
                Uses HuggingFace <code class="text-purple-300">cross-encoder/ms-marco-MiniLM-L-6-v2</code> to score query-document candidate pairs jointly, eliminating vector cosine search hallucinations and ensuring high-precision financial citation recall.
              </p>
            </div>

            <!-- Pillar 3: Adaptive Inference Routing -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
              <div class="flex items-center gap-2 text-white font-semibold text-xs">
                <Cpu class="w-4 h-4 text-amber-400" />
                <span>3. Adaptive LLM Router (Ollama / OpenRouter)</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed">
                Zero-vendor-lockin protocol-driven routing. Operates completely locally via Ollama (Llama 3 / Mistral) in offline/air-gapped development, or routes seamlessly to cloud endpoints (OpenRouter / OpenAI) in production with SSE token streaming.
              </p>
            </div>

            <!-- Pillar 4: Forensic Quantitative Pipeline -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
              <div class="flex items-center gap-2 text-white font-semibold text-xs">
                <ShieldCheck class="w-4 h-4 text-emerald-400" />
                <span>4. Forensic Quantitative Engines</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed">
                Custom implementations of the 8-variable Beneish M-Score probabilistic model, difflib SequenceMatcher opcode language drift engine, and cross-encoder executive tone decoupling radar.
              </p>
            </div>

            <!-- Pillar 5: Testing & Reliability -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
              <div class="flex items-center gap-2 text-white font-semibold text-xs">
                <CheckCircle2 class="w-4 h-4 text-teal-400" />
                <span>5. 144 Automated Tests & CI Automation</span>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed">
                Comprehensive unit and integration test coverage across math formulas, division-by-zero safeguards, regex safety, and SSE streaming lifecycle, verified via GitHub Actions CI pipeline on every PR.
              </p>
            </div>

          </div>

          <!-- Lead Systems Architect Contact -->
          <div class="p-4 rounded-2xl bg-slate-800/80 border border-white/10 text-center space-y-2">
            <h5 class="text-xs font-bold text-white">Enterprise AI & Full-Stack Systems Inquiries</h5>
            <p class="text-[11px] text-slate-300">
              Robust, high-performance web applications and embedded AI solutions tailored to complex enterprise domains.
            </p>
            <div class="pt-1">
              <a 
                href="mailto:faycal.raghibi@etu.imt-nord-europe.fr"
                class="apple-press inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-xs"
              >
                <span>Contact Lead Systems Architect</span>
                <ExternalLink class="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

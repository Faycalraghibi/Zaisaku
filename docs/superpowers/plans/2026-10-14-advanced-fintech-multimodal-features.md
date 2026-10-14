# Advanced Multimodal Financial AI Features & Institutional Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Zaisaku into an institutional-grade, client-winning portfolio application by implementing:
1. Automated Financial Table & Metric Extraction Studio with YoY variance calculation and CSV export.
2. Multimodal Earnings Call Audio Simulator with animated waveform visualizer, synchronized speaker transcripts, and live tone sentiment gauge.
3. Interactive AI Prompt & RAG Laboratory (Sandbox) with model latency benchmarks, token metrics, and temperature tuning.
4. Print-Ready Institutional Due Diligence Memorandum Preview & Export.

**Architecture:**
- Backend adds three specialized services: `TableExtractor` for parsing structured financial statements and computing YoY variances, `CallSimulator` for timestamped earnings call speaker events and sentiment decoupling, and `SandboxBenchmark` for evaluating retrieval latency and token efficiency across LLM engines.
- Frontend adds an interactive financial statements grid, an animated HTML5 canvas audio waveform player with transcript syncing, a prompt testing sandbox modal, and a print-ready memo preview modal.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Pytest, Vue 3.5, Vite 8, Tailwind CSS v4, Lucide Vue Next, HTML5 Canvas API.

**Spec:** User request: "more features" to showcase advanced AI capabilities to prospective enterprise clients across finance and general domains.

## Global Constraints

- Preserve all 144 existing backend tests with zero regressions.
- All code in `backend/` must pass `ruff check backend/` cleanly with zero errors.
- Frontend must build cleanly with `npm --prefix frontend run build` in <2s with zero errors.
- Adhere strictly to `apple-design` foundations: fluid pointer-down tactile feedback, specular translucency, critically damped spring motion, and reduced-motion accessibility.
- Landing screen remains the Company Due Diligence Hub.

## Review Focus

1. **Table Extraction YoY Variance Division by Zero:** When prior period revenue or metric is zero or negative, handle variance calculation without throwing `ZeroDivisionError`.
2. **Audio Waveform Canvas Cleanup:** Ensure `requestAnimationFrame` audio animation loop is properly canceled on component unmount or pause to prevent memory leaks.
3. **Structured Table CSV Export:** Handle quotes, commas, and newlines in cell data properly using RFC 4180 CSV escaping.
4. **Playback Speed Synchronization:** Synchronize transcript scrolling accurately at 1x, 1.25x, 1.5x, and 2x playback speeds.
5. **Print CSS Styling:** Ensure `@media print` rules cleanly format the institutional memorandum for PDF export without dark mode artifacts.

---

### Task 1: Financial Table & Metric Extraction Engine Backend

**Files:**
- Create: `backend/src/zaisaku/forensics/table_extractor.py`
- Modify: `backend/src/zaisaku/api/routers/forensics.py`
- Test: `backend/tests/unit/test_table_extractor.py`

- [ ] **Step 1.1**: Write failing unit tests for `TableExtractor` in `backend/tests/unit/test_table_extractor.py`.
- [ ] **Step 1.2**: Run pytest to verify test failure.
- [ ] **Step 1.3**: Implement `TableExtractor` in `backend/src/zaisaku/forensics/table_extractor.py`.
- [ ] **Step 1.4**: Add `GET /api/forensics/tables/{ticker}` in `backend/src/zaisaku/api/routers/forensics.py`.
- [ ] **Step 1.5**: Run pytest and ruff check to verify tests pass and code is clean.
- [ ] **Step 1.6**: Commit with message `feat(forensics): add structured financial table extraction engine and API`.

---

### Task 2: Multimodal Earnings Call Audio & Transcript Backend

**Files:**
- Create: `backend/src/zaisaku/forensics/call_simulator.py`
- Modify: `backend/src/zaisaku/api/routers/forensics.py`
- Test: `backend/tests/unit/test_call_simulator.py`

- [ ] **Step 2.1**: Write failing unit tests for `CallSimulator` in `backend/tests/unit/test_call_simulator.py`.
- [ ] **Step 2.2**: Run pytest to verify test failure.
- [ ] **Step 2.3**: Implement `CallSimulator` in `backend/src/zaisaku/forensics/call_simulator.py`.
- [ ] **Step 2.4**: Add `GET /api/forensics/calls/{ticker}` in `backend/src/zaisaku/api/routers/forensics.py`.
- [ ] **Step 2.5**: Run pytest and ruff check to verify tests pass and code is clean.
- [ ] **Step 2.6**: Commit with message `feat(forensics): add multimodal earnings call simulator and transcript API`.

---

### Task 3: AI Prompt & RAG Benchmark Sandbox Backend

**Files:**
- Create: `backend/src/zaisaku/forensics/sandbox.py`
- Modify: `backend/src/zaisaku/api/routers/forensics.py`
- Test: `backend/tests/unit/test_sandbox.py`

- [ ] **Step 3.1**: Write failing unit tests for `SandboxBenchmark` in `backend/tests/unit/test_sandbox.py`.
- [ ] **Step 3.2**: Run pytest to verify test failure.
- [ ] **Step 3.3**: Implement `SandboxBenchmark` in `backend/src/zaisaku/forensics/sandbox.py`.
- [ ] **Step 3.4**: Add `POST /api/forensics/sandbox/benchmark` in `backend/src/zaisaku/api/routers/forensics.py`.
- [ ] **Step 3.5**: Run pytest and ruff check to verify tests pass and code is clean.
- [ ] **Step 3.6**: Commit with message `feat(forensics): add prompt engineering and RAG benchmark sandbox API`.

---

### Task 4: Interactive Financial Table & Metric Extraction Studio Frontend

**Files:**
- Create: `frontend/src/components/FinancialTableExtractor.vue`
- Modify: `frontend/src/components/CompanyHub.vue`

- [ ] **Step 4.1**: Build `FinancialTableExtractor.vue` with multi-statement tabs (Income Statement, Segment Revenue, Balance Sheet), YoY variance highlighting, and CSV export.
- [ ] **Step 4.2**: Integrate `FinancialTableExtractor.vue` into `CompanyHub.vue`.
- [ ] **Step 4.3**: Verify frontend build with `npm --prefix frontend run build`.
- [ ] **Step 4.4**: Commit with message `feat(ui): add interactive financial table extraction studio`.

---

### Task 5: Multimodal Audio Earnings Call Simulator with Live Waveform Frontend

**Files:**
- Create: `frontend/src/components/AudioCallSimulator.vue`
- Modify: `frontend/src/components/CompanyHub.vue`

- [ ] **Step 5.1**: Build `AudioCallSimulator.vue` with HTML5 Canvas audio waveform, play/pause scrubber, speed controls, synchronized transcript, and real-time sentiment meter.
- [ ] **Step 5.2**: Integrate `AudioCallSimulator.vue` into `CompanyHub.vue`.
- [ ] **Step 5.3**: Verify frontend build with `npm --prefix frontend run build`.
- [ ] **Step 5.4**: Commit with message `feat(ui): add multimodal earnings call simulator with live audio waveform`.

---

### Task 6: AI Prompt Sandbox Modal & Print-Ready Memo Preview Frontend

**Files:**
- Create: `frontend/src/components/ForensicSandboxModal.vue`
- Create: `frontend/src/components/InstitutionalReportModal.vue`
- Modify: `frontend/src/components/CompanyHub.vue`

- [ ] **Step 6.1**: Build `ForensicSandboxModal.vue` with model selector, temperature controls, live latency meters, and token efficiency statistics.
- [ ] **Step 6.2**: Build `InstitutionalReportModal.vue` with print-ready institutional report layout, printable CSS, and PDF export trigger.
- [ ] **Step 6.3**: Mount and wire both modals in `CompanyHub.vue`.
- [ ] **Step 6.4**: Verify full test suite (`pytest backend/tests/`) and frontend build (`npm --prefix frontend run build`).
- [ ] **Step 6.5**: Commit with message `feat(ui): add AI sandbox playground and print-ready institutional memo preview`.

# Zaisaku

> **This README is written as a briefing for Claude (claude.ai).**
> It contains everything you need to understand the project, its architecture, stack, conventions, and current state — so you can help me build, debug, and extend it effectively.

---

## What is Zaisaku?

Zaisaku is a **Retrieval-Augmented Generation (RAG) pipeline** designed to make unstructured financial documents queryable in natural language.

A user uploads a PDF annual report, an HTML news article, or a plain text prospectus. Zaisaku indexes it, and the user can then ask questions like:

> *"What was the net income of BNP Paribas in FY2023?"*
> *"What risks are mentioned in the prospectus for this bond?"*
> *"Summarize the CEO's outlook for next year."*

The system retrieves the most relevant document chunks, reranks them with a cross-encoder, and feeds them into an LLM that produces a sourced, grounded answer in JSON format.

---

## Why it exists

This project was built to demonstrate end-to-end RAG engineering skills for a role in the **Trading & Financial Information** division at Worldline (Seclin, France), which focuses on:
- Giving investors access to information in unstructured financial documents
- Aggregating and cross-referencing financial data flows
- Building AI features on top of structured + unstructured data

Zaisaku is a personal MVP that directly addresses this problem domain.

---

## Full Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | **Flask 3 + Flask-RESTX** | Lightweight Python REST framework |
| Vector DB | **ChromaDB** | Simple, local-first vector store, no cloud dependency |
| Embeddings | **sentence-transformers/all-MiniLM-L6-v2** | Fast, accurate, runs locally |
| Reranker | **cross-encoder/ms-marco-MiniLM-L-6-v2** | Re-scores top-10 candidates → top-3 |
| LLM (dev) | **Ollama — mistral:7b** | Zero cost, fully local, no API key needed |
| LLM (prod) | **OpenRouter — google/gemini-flash** | Cloud fallback with OpenAI-compatible API |
| Frontend | **VueJS 3 + Vite + TailwindCSS** | Modern reactive UI, fast dev server |
| Evaluation | **RAGAS** | Measures faithfulness, relevancy, precision, recall |
| Deploy | **Docker Compose** | One command to run the full stack |

---

## Project Structure

```
zaisaku/
├── backend/
│   ├── ingestion/
│   │   ├── loader.py         # Parses PDF (PyMuPDF), HTML (BeautifulSoup), TXT
│   │   ├── chunker.py        # Sliding window chunking — 512 tokens, overlap 64
│   │   └── embedder.py       # sentence-transformers wrapper, returns List[float]
│   ├── retrieval/
│   │   ├── vector_store.py   # ChromaDB client — upsert, search, delete, list
│   │   └── reranker.py       # CrossEncoder — reranks top-10 → top-3
│   ├── generation/
│   │   ├── llm.py            # LLMRouter: ENV=dev → Ollama, ENV=prod → OpenRouter
│   │   └── prompt.py         # Finance system prompt + RAG template (JSON output)
│   ├── api/
│   │   ├── app.py            # Flask app factory, CORS, Flask-RESTX init
│   │   └── routes.py         # All endpoints: /ingest /query /documents /health
│   ├── tests/
│   │   └── test_ragas.py     # RAGAS evaluation suite with quality thresholds
│   ├── config.py             # All env vars in one place, loaded from .env
│   ├── run.py                # Entrypoint: creates app, binds to 0.0.0.0:5000
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.vue   # Chat UI, message history, confidence bar
│   │   │   ├── SourceViewer.vue    # Right panel, shows reranked chunks + scores
│   │   │   └── UploadZone.vue      # Drag & drop modal, calls /ingest
│   │   ├── services/
│   │   │   └── api.js              # All fetch calls: ingest, query, list, delete, health
│   │   ├── App.vue                 # Root layout: header, chat, source panel, upload modal
│   │   ├── main.js                 # Vue createApp mount
│   │   └── style.css               # Tailwind base + custom scrollbar
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js              # Dev proxy: /api → localhost:5000
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── Dockerfile                  # Multi-stage: Vite build → Nginx serve
├── docker-compose.yml              # 3 services: chromadb, backend, frontend
├── .env.example                    # All required env vars with defaults
├── .gitignore
└── README.md                       # This file
```

---

## Data Flow (step by step)

### Ingestion
```
User uploads file (POST /api/ingest)
  → DocumentLoader.load()        # raw text + metadata extraction
  → Chunker.chunk()              # sliding window 512 tok, overlap 64
  → Embedder.embed()             # batch encode all chunks
  → VectorStore.upsert()         # store in ChromaDB with metadata
  ← {doc_id, filename, chunks, status: "indexed"}
```

### Query
```
User asks question (POST /api/query)
  → Embedder.embed_one(question)       # embed the query
  → VectorStore.search(top_k=10)       # cosine similarity search
  → Reranker.rerank(top_k=3)           # cross-encoder rescoring
  → build_rag_prompt(query, chunks)    # inject context into template
  → LLMRouter.generate()               # Ollama or OpenRouter
  → JSON parse LLM response
  ← {answer, confidence, sources, model, env}
```

---

## Key Files to Know

### `backend/config.py`
Single source of truth for all configuration. Reads from `.env`. Controls:
- `ENV` — switches LLM backend (`"dev"` = Ollama, `"prod"` = OpenRouter)
- `CHUNK_SIZE`, `CHUNK_OVERLAP` — chunking parameters
- `RETRIEVAL_TOP_K`, `RERANK_TOP_K` — retrieval depth
- All ChromaDB, Flask, CORS settings

### `backend/generation/llm.py`
`LLMRouter` selects backend at init time based on `ENV`.
- `_OllamaBackend` — calls `POST /api/chat` on `OLLAMA_BASE_URL`
- `_OpenRouterBackend` — uses `openai` SDK pointed at OpenRouter's base URL
- Both return `{"text": str, "model": str, "env": str}`

### `backend/generation/prompt.py`
The LLM is instructed to respond **only in JSON** with this schema:
```json
{
  "answer": "...",
  "confidence": 0.0,
  "sources_used": ["filename1.pdf"]
}
```
If the LLM doesn't comply, `routes.py` catches the `JSONDecodeError` and falls back gracefully.

### `backend/retrieval/vector_store.py`
ChromaDB uses **cosine similarity** (`hnsw:space: cosine`).
Search returns `distance` (0 = identical, 1 = opposite), converted to `score = 1 - distance`.

### `frontend/src/services/api.js`
Five functions: `ingestDocument`, `queryDocuments`, `listDocuments`, `deleteDocument`, `healthCheck`.
All call `BASE_URL` from `VITE_API_URL` env var (defaults to `http://localhost:5000/api`).

---

## Environment Variables

```bash
# .env
ENV=dev                          # "dev" = Ollama | "prod" = OpenRouter

# Ollama (dev)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral:7b

# OpenRouter (prod)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-flash-1.5

# ChromaDB
CHROMA_HOST=chromadb             # service name in docker-compose
CHROMA_PORT=8000
CHROMA_COLLECTION=zaisaku_docs

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Flask
FLASK_PORT=5000
SECRET_KEY=change_me
CORS_ORIGIN=http://localhost:5173
```

---

## Running Locally

### Prerequisites
- Docker + Docker Compose
- Ollama running locally with `ollama pull mistral`
- (prod only) OpenRouter API key

### Start everything
```bash
git clone https://github.com/Faycalraghibi/Zaisaku
cd Zaisaku
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API docs (Swagger) | http://localhost:5000/api/docs |
| ChromaDB | http://localhost:8000 |

### Run backend only (no Docker)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python run.py
```

### Run frontend only (no Docker)
```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Body | Returns |
|---|---|---|---|
| GET | `/api/health` | — | `{status, env}` |
| POST | `/api/ingest` | `multipart/form-data` file | `{doc_id, filename, chunks, status}` |
| POST | `/api/query` | `{question, filter?}` | `{answer, confidence, sources, model, env}` |
| GET | `/api/documents` | — | `{documents: [...]}` |
| DELETE | `/api/documents/<doc_id>` | — | `{deleted_chunks: int}` |

Full interactive docs at `/api/docs` (Flask-RESTX Swagger UI).

---

## Evaluation

```bash
cd backend
pytest tests/test_ragas.py -v
```

RAGAS metrics tracked:
- **faithfulness** — is the answer supported by the retrieved chunks?
- **answer_relevancy** — does the answer address the question?
- **context_precision** — are the retrieved chunks actually relevant?
- **context_recall** — are all relevant chunks retrieved?

Minimum thresholds enforced: `faithfulness >= 0.7`, `answer_relevancy >= 0.7`.

---

## Current State

### Done
- Full ingestion pipeline (PDF, HTML, TXT)
- ChromaDB upsert + cosine search
- Cross-encoder reranking
- Dual LLM backend (Ollama dev / OpenRouter prod)
- Finance-specific prompt with structured JSON output
- Flask-RESTX API with Swagger docs
- VueJS 3 chat UI with source viewer and upload modal
- Docker Compose full-stack deployment
- RAGAS evaluation suite

### Not yet implemented
- Streaming responses (SSE) — LLM output currently buffered
- Multi-document comparison queries
- Financial entity extraction (NER on company names, tickers, dates)
- Authentication / API key protection
- Persistent conversation history
- Document metadata filtering in the UI

---

## Conventions to Follow When Helping Me

- **Python style**: type hints everywhere, dataclasses for data models, no bare `except`
- **Flask**: always use the app factory pattern (`create_app()`), never global `app`
- **Imports**: absolute imports from project root (e.g. `from ingestion.loader import ...`)
- **Config**: all magic values go in `config.py`, never hardcoded inline
- **Errors**: Flask routes abort with `ns.abort(code, message)`, never raise raw exceptions
- **Frontend**: Composition API only (`<script setup>`), no Options API
- **CSS**: Tailwind utility classes only, no custom CSS except in `style.css`
- **Commits**: conventional commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`)

---

## Useful Commands

```bash
# Rebuild after changing requirements
docker compose build backend

# Watch backend logs
docker compose logs -f backend

# Reset ChromaDB (wipe all vectors)
docker compose down -v && docker compose up

# Run a quick ingest test
curl -X POST http://localhost:5000/api/ingest \
  -F "file=@tests/sample_report.pdf"

# Run a quick query test
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the net income?"}'
```
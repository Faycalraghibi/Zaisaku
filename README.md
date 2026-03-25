# Zaisaku

Zaisaku is a modern, modular Retrieval-Augmented Generation (RAG) pipeline optimized for analyzing and chatting with financial documents. Built with a production-ready FastAPI backend and a responsive Vue 3 + Tailwind CSS frontend.

## Features

- **Multi-Format Ingestion**: Natively processes sliding-window chunks from PDF, HTML, and TXT files.
- **Protocol-Driven Architecture**: Easily swap components (Embedders, Vector Stores, Rerankers, LLMs) through defined Python Protocols.
- **Cross-Encoder Reranking**: Uses Hugging Face cross-encoders to re-score vector search candidates for maximum relevance.
- **LLM Routing**: Automatically routes inference to local models (Ollama) in development or remote APIs (OpenRouter) in production.
- **Docker Ready**: Fully containerized multi-container setup (Nginx, FastAPI, ChromaDB) via Docker Compose.

## Quick Start

### 1. Environment Setup
Configure your environment variables (see internal configurations in `backend/src/zaisaku/config.py`).
* If using OpenRouter, set `OPENROUTER_API_KEY`.
* If using Ollama, ensure it is running locally.

### 2. Run with Docker Compose
The easiest way to start the entire stack:
```bash
docker compose up -d --build
```
- **UI**: http://localhost
- **API Docs**: http://localhost:8080/api/docs

### 3. Local Development (Without Docker)
Instead of Docker, you can run the services natively:

**Terminal 1 (Backend):**
```bash
cd backend
pip install -e .
python run.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

## Testing & Evaluation
Zaisaku embraces Test-Driven Development (TDD) with 100% feature coverage:
```bash
cd backend
pytest tests/ -v
```

For RAG pipeline heuristic validation, execute the Ragas script:
```bash
python backend/scripts/evaluate.py
```
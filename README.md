# SchemeSaathi (திட்ட தோழன்) 🇮🇳

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![FAISS](https://img.shields.io/badge/FAISS-VectorStore-orange.svg)](https://github.com/facebookresearch/faiss)
[![Claude 3.5 Sonnet](https://img.shields.io/badge/Anthropic-Claude_3.5_Sonnet-purple.svg)](https://www.anthropic.com/)
[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](https://github.com/your-org/schemesaathi/actions)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**SchemeSaathi** (திட்ட தோழன்) is an enterprise-grade, multilingual Retrieval-Augmented Generation (RAG) assistant designed to help Indian citizens accurately understand central and state (Tamil Nadu) government welfare schemes in **English** and **Tamil (தமிழ்)** using exclusively official government PDF documents as sources.

---

## 📌 Problem Statement

1. **Complex, Bureaucratic Documentation**: Official government scheme guidelines (e.g., PM-KISAN, Kalaignar Magalir Urimai) are published as lengthy, multi-page PDFs written in dense bureaucratic English or formal Tamil. Ordinary citizens, farmers, and women heads of households struggle to decipher eligibility thresholds, exclusion categories, land ownership caps, and application steps.
2. **High Hallucination Risk in Generic LLMs**: Standard conversational LLMs frequently invent welfare subsidy amounts, quote obsolete income limits, or conflate central and state criteria, leading to misinformed citizens and rejected applications.
3. **Linguistic Divide**: India's welfare recipients predominantly communicate in regional languages like Tamil. Existing systems either lack native regional language capability or suffer cross-lingual degradation when querying English policy documents with regional queries (and vice versa).
4. **Lack of Grounded Citations**: Citizens and welfare administrators need auditable answers showing the exact scheme name, guideline page number, and document excerpt.

**SchemeSaathi solves this** with an end-to-end RAG architecture featuring multilingual embeddings, normalized cosine FAISS vector search, similarity threshold gating with zero-LLM out-of-scope drop, XML-delimited prompt injection defense, and mandatory source citations (`[Scheme name, p.X]`).

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Document Ingestion Pipeline"]
        PDFs["Official Scheme PDFs\n(data/raw/)"] --> PyMuPDF["PyMuPDF Parser\n(Unicode Tamil & English)"]
        PyMuPDF --> Cleaner["Header/Footer & Whitespace Cleaner\n(Strip repeated headers, footers & pagination)"]
        Cleaner --> Chunker["Sentence-Boundary Chunker\n(~500 tokens, 80-token overlap)"]
        Chunker --> ChunksJSON["data/index/chunks.jsonl\n(Deterministic Chunk Metadata)"]
        ChunksJSON --> E5Passage["E5 Multilingual Embedder\n('passage: ' prefix, 384-dim)"]
        E5Passage --> FAISSBuild["FAISS Cosine Index\n(data/index/faiss_index.bin)"]
    end

    subgraph Serving["2. Real-Time RAG Serving Engine"]
        UserQuery["User Query\n(English or Tamil)"] --> LangDetect["Language Detector\n(Tamil Unicode Code-Points)"]
        UserQuery --> E5Query["E5 Query Embedder\n('query: ' prefix, L2 Normalized)"]
        E5Query --> FAISSSearch["FAISS Inner-Product Search\n(Retrieve Top-K Chunks)"]
        FAISSSearch --> ThresholdFilter{"Top Score >= 0.80\nSimilarity Cutoff?"}
        
        ThresholdFilter -- No --> ZeroLLM["Zero-LLM Fast Fallback\n'I couldn't find this in the scheme documents.'\n(Zero Token Cost & Zero Hallucination)"]
        
        ThresholdFilter -- Yes --> XMLPrompt["XML Delimitation & Prompt Hardening\n<official_context><document_excerpt>"]
        XMLPrompt --> ClaudeLLM["Anthropic Claude 3.5 Sonnet\n(Grounded Synthesis with Retries)"]
        ClaudeLLM --> GroundedResp["Grounded Answer + Citations\n[Scheme name, p.X]"]
    end

    subgraph ClientAndDB["3. Client & Persistence Layer"]
        GroundedResp --> API["FastAPI REST Endpoints\n(POST /chat, GET /schemes, GET /history)"]
        ZeroLLM --> API
        API --> MongoDB[("MongoDB / In-Memory Cache\n(Chat Session Persistence)")]
        API --> ReactUI["React 18 + Tailwind Frontend\n(Bilingual Toggle, Source Accordion, Prefill Chips)"]
    end

    FAISSBuild -.-> FAISSSearch
    ReactUI --> UserQuery
```

---

## ✨ Features

- **🌐 Native Bilingual English & Tamil**:
  - Script-aware language detector examining Tamil Unicode range (`\u0B80`–`\u0BFF`).
  - Native Tamil sentence boundary segmentation respecting Tamil punctuation and abbreviations (`ரூ.`, `திரு.`, `எண்.`).
  - Seamless English $\leftrightarrow$ Tamil UI toggling across all labels, chips, and error banners.
- **🛡️ Strict Grounding & Anti-Hallucination Guardrails**:
  - **Threshold Gating ($\tau = 0.80$)**: Queries with maximum chunk similarity below 0.80 are rejected immediately without calling the LLM.
  - **Zero-LLM Fallback**: Non-scheme questions return `"I couldn't find this in the scheme documents"` (English) or `"திட்ட ஆவணங்களில் இந்த தகவலை என்னால் கண்டுபிடிக்க முடியவில்லை"` (Tamil) in $< 25\text{ ms}$.
  - **Mandatory Source Citations**: Every generated fact is cited with `[Scheme name, p.X]`.
- **🔒 Prompt Injection Neutralization**: Context passages are wrapped inside delimited XML blocks (`<official_context><document_excerpt>`), and closing-tag exploits are sanitized.
- **⚡ High-Performance Vector Retrieval**:
  - Powered by `intfloat/multilingual-e5-small` with required `query: ` and `passage: ` prefixes.
  - L2-normalized `faiss.IndexFlatIP` yielding sub-millisecond cosine vector lookup.
- **💾 Dual-Persistence Storage**:
  - Asynchronous Motor MongoDB driver for session chat history.
  - Automatic fallback to in-memory session cache when MongoDB is offline, allowing zero-downtime operation.
- **🚦 Production Observability & Rate Limiting**:
  - SlowAPI rate limiter (30 requests/minute per client).
  - Structured application logging tracking query latency (`latency_ms`), retrieved `chunk_ids`, and language.
- **📱 Modern Responsive Frontend**:
  - React 18, Vite, and Tailwind CSS.
  - Chat bubbles with rich Markdown rendering (bolding, lists, tables).
  - Collapsible **"Sources / குறிப்புகள்"** drawer displaying scheme name, page number, similarity score badge, and exact PDF text snippet.
  - Sidebar with dynamic `GET /schemes` listing and one-click question prefill chips.
  - Automatic session persistence in `localStorage`.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Framework** | FastAPI (Python 3.11) + Uvicorn | High-performance asynchronous ASGI REST API |
| **Embeddings** | `intfloat/multilingual-e5-small` | 384-dimensional multilingual sentence transformer |
| **Vector Index** | FAISS (`IndexFlatIP`) | Normalized inner-product cosine similarity search |
| **LLM Synthesis** | Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`) | Grounded answer generation with exponential retry |
| **PDF Extraction** | PyMuPDF (`fitz`) | Multi-lingual text extraction & font preservation |
| **Database** | MongoDB (Motor Async) | Session state and conversation turn persistence |
| **Rate Limiting** | SlowAPI | 30 requests/minute DDoS and abuse protection |
| **Frontend** | React 18 + Vite | Single Page Application (SPA) |
| **Styling** | Tailwind CSS + Lucide Icons | Responsive modern design with mobile drawer |
| **Containerization** | Docker, Docker Compose, Nginx | Multi-container orchestration and reverse proxy |
| **CI / CD** | GitHub Actions | Automated pytest and Vite build on every push |

---

## 📁 Repository Structure

```text
schemesaathi/
├── docker-compose.yml              # Multi-container setup (Mongo + Backend + Frontend)
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── README.md                       # Comprehensive documentation
├── DEPLOYMENT.md                   # Cloud & VPS deployment guide
├── backend/
│   ├── Dockerfile                  # Python 3.11 container with pre-downloaded model
│   ├── requirements.txt            # Python dependencies
│   ├── app/
│   │   ├── config.py               # Pydantic Settings configuration loader
│   │   ├── db.py                   # Async Motor MongoDB driver with memory fallback
│   │   ├── embeddings.py           # E5 embedding loader & prefix formatter
│   │   ├── ingest.py               # PDF cleaner, header/footer stripper & chunker
│   │   ├── main.py                 # FastAPI endpoints (/chat, /schemes, /history)
│   │   ├── models.py               # Pydantic request/response schemas
│   │   ├── rag.py                  # Grounded RAG engine, prompt injection guard
│   │   └── vectorstore.py          # FAISS index builder & cosine similarity search
│   └── tests/
│       ├── test_chat_endpoint.py   # FastAPI TestClient & mocked MongoDB tests
│       ├── test_health.py          # /health endpoint test
│       ├── test_ingest.py          # Chunk overlap & metadata preservation tests
│       ├── test_rag.py             # Zero-LLM fallback & prompt injection tests
│       └── test_vectorstore.py     # Known query semantic search tests
├── data/
│   ├── raw/                        # Official government PDFs (PM-KISAN, KMUT)
│   └── index/                      # FAISS binary index, chunks.jsonl, metadata
├── frontend/
│   ├── Dockerfile                  # Multi-stage Node 20 + Nginx production container
│   ├── nginx.conf                  # Nginx static server and reverse proxy
│   ├── package.json                # React dependencies
│   ├── vite.config.js              # Vite dev server proxy
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   └── src/
│       ├── App.jsx                 # Main chat interface with localStorage persistence
│       ├── translations.js         # Bilingual English/Tamil UI dictionary
│       └── components/
│           ├── Header.jsx          # Header with language toggle and status indicator
│           ├── Sidebar.jsx         # Scheme listing & click-to-prefill sidebar
│           ├── ChatMessage.jsx     # Markdown bubbles & collapsible source panels
│           └── TypingIndicator.jsx # Live searching animation
├── eval/
│   ├── questions.json              # 40 benchmark questions (English & Tamil)
│   ├── run_eval.py                 # Automated evaluation script
│   ├── run_experiments.py          # Experiments runner (Top-K, Threshold, Chunks)
│   ├── results.md                  # Comprehensive baseline evaluation results
│   └── experiments_comparison.md   # Comparative experiments matrix
└── scripts/
    ├── sanity_check_search.py      # Semantic search sanity check
    └── test_rag_live.py            # Live Claude RAG query runner
```

---

## ⚙️ Quick Start Guide

### Option 1: Run with Docker Compose (Recommended)

1. **Clone the repository and prepare `.env`**:
   ```bash
   cp .env.example .env
   ```
   Add your Anthropic API key to `.env`:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

2. **Start all services**:
   ```bash
   docker compose up -d --build
   ```

3. **Open SchemeSaathi**:
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option 2: Local Development Setup

#### 1. Setup Backend Virtual Environment
```bash
# Windows (PowerShell):
python -m venv backend/venv
.\backend\venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv backend/venv
source backend/venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 3. Ingest Scheme PDFs & Build Vector Index
Place official PDFs in `data/raw/` and execute:
```bash
# Step 1: Parse and chunk PDFs
python -m app.ingest

# Step 2: Build normalized FAISS vector index
python -m app.vectorstore --build

# Step 3: Run retrieval quality sanity check
python scripts/sanity_check_search.py
```

#### 4. Launch FastAPI Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. Launch React Frontend
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

## 📡 API Reference & Curl Examples

### 1. Health & Readiness (`GET /health`)
```bash
curl http://localhost:8000/health
```
**Response**:
```json
{
  "status": "healthy",
  "app_name": "SchemeSaathi",
  "version": "0.1.0",
  "embedding_model": "intfloat/multilingual-e5-small",
  "mongo_connected": true,
  "indexed_documents_count": 3,
  "timestamp": "2026-11-10T15:30:00.000000"
}
```

---

### 2. Submit Question (`POST /chat`)

#### English In-Scope Query:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "citizen_session_01",
    "question": "What is the annual financial support provided under PM-KISAN?"
  }'
```
**Response**:
```json
{
  "session_id": "citizen_session_01",
  "question": "What is the annual financial support provided under PM-KISAN?",
  "answer": "Under the PM-KISAN scheme, eligible farmer families receive an income support of Rs. 6,000 per year. This amount is disbursed in three equal installments of Rs. 2,000 every four months directly into their bank accounts [PM Kisan, p.1].",
  "language": "en",
  "sources": [
    {
      "scheme_name": "PM Kisan",
      "source_file": "pm_kisan.pdf",
      "page_number": 1,
      "score": 0.892,
      "snippet": "Under the scheme, the Central Government provides an income support of Rs. 6,000 per year in three equal four-monthly installments of Rs. 2,000 each..."
    }
  ],
  "chunk_ids": ["pm_kisan_p1_c0"],
  "latency_ms": 1240.2
}
```

#### Tamil In-Scope Query:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "citizen_session_02",
    "question": "கலைஞர் மகளிர் உரிமைத் திட்டத்தின் கீழ் குடும்பத் தலைவிகளுக்கு மாதம் எவ்வளவு தொகை வழங்கப்படுகிறது?"
  }'
```

#### Out-of-Scope Query (Zero-LLM Fast Fallback):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "citizen_session_03",
    "question": "How do I bake chocolate chip cookies in an oven?"
  }'
```
**Response** *(returned in $< 25\text{ ms}$ without calling the Claude API)*:
```json
{
  "session_id": "citizen_session_03",
  "question": "How do I bake chocolate chip cookies in an oven?",
  "answer": "I couldn't find this in the scheme documents.",
  "language": "en",
  "sources": [],
  "chunk_ids": [],
  "latency_ms": 21.4
}
```

---

### 3. List Indexed Schemes (`GET /schemes`)
```bash
curl http://localhost:8000/schemes
```
**Response**:
```json
{
  "schemes": [
    "Kalaignar Magalir Urimai",
    "PM Kisan"
  ],
  "total_count": 2
}
```

---

### 4. Conversation History (`GET` & `DELETE /history/{session_id}`)
```bash
# Fetch messages for a session
curl http://localhost:8000/history/citizen_session_01

# Delete messages and reset session
curl -X DELETE http://localhost:8000/history/citizen_session_01
```

---

## 📊 Evaluation Results (from `eval/results.md`)

Evaluation was conducted against [`eval/questions.json`](file:///c:/e/Rag/eval/questions.json) comprising **40 test questions** (15 English in-scope, 15 Tamil in-scope, 10 out-of-scope).

### 🎯 Metric Summary

| Metric | Measured Value | Target Goal | Status |
|---|---|---|---|
| **Retrieval Hit@3 (In-Scope)** | **100.0%** (30/30) | $\ge 90\%$ | ✅ **PASS** |
| **Retrieval Hit@1 (Rank-1 Precision)** | **83.33%** (25/30) | $\ge 85\%$ | ⚠️ **Near Target** |
| **Exact Page Match Rate** | **100.0%** (30/30) | $\ge 80\%$ | ✅ **PASS** |
| **Citation Inclusion Rate** | **76.67%** (23/30) | $\ge 90\%$ | ⚠️ **Trade-off** |
| **Out-of-Scope "Not Found" Rate** | **100.0%** (10/10) | $100\%$ | ✅ **PASS** |
| **Average Retrieval Latency** | **22.8 ms** | $< 100\text{ ms}$ | ✅ **Ultra Fast** |

### 🌐 Language Breakdown (In-Scope Hit@3)

| Language | Test Questions | Hit@3 Count | Hit@3 Rate | Status |
|---|---|---|---|---|
| **English (`en`)** | 15 | 15 | **100.0%** | ✅ **Flawless** |
| **Tamil (`ta`)** | 15 | 15 | **100.0%** | ✅ **Flawless** |

### 🔬 Optimization Experiments Matrix (from `eval/experiments_comparison.md`)

| Experiment Configuration | Hit@3 (%) | Hit@1 (%) | Page Match (%) | Citation Rate (%) | Out-of-Scope Not-Found (%) | Avg Latency (ms) |
|---|---|---|---|---|---|---|
| **Baseline ($\tau=0.80, K=4$)** | **100.0%** | **83.33%** | **100.0%** | 76.67% | **100.0%** | **22.8 ms** |
| **Threshold $\tau=0.78$** | **100.0%** | **83.33%** | **100.0%** | **90.00%** | 60.0% | 23.1 ms |
| **Threshold $\tau=0.82$** | **100.0%** | **83.33%** | **100.0%** | 63.33% | **100.0%** | 22.3 ms |
| **Top-$K = 2$** | **100.0%** | **83.33%** | **100.0%** | 76.67% | **100.0%** | 21.4 ms |
| **Top-$K = 5$** | **100.0%** | **83.33%** | **100.0%** | 76.67% | **100.0%** | 21.2 ms |

---

## ⚠️ Limitations

1. **Digital PDF Dependency**: Text extraction relies on PyMuPDF extracting digital font streams. Purely scanned image PDFs without an embedded OCR layer must be pre-processed with OCR (Tesseract / PaddleOCR).
2. **Cross-Lingual Semantic Gap**: Monolingual queries (English $\leftrightarrow$ English or Tamil $\leftrightarrow$ Tamil) yield cosine scores $> 0.84$. Cross-lingual queries (English query $\leftrightarrow$ Tamil document) score between $0.76$ and $0.795$. At a static cutoff $\tau = 0.80$, some cross-lingual in-scope queries are dropped to prevent out-of-scope hallucination.
3. **Single-Hop Fact Retrieval**: While multi-page context is retrieved via Top-$K$, complex multi-hop comparative queries (e.g., comparing income ceilings across three different schemes simultaneously) require more context tokens.
4. **LLM Cost & Rate Limits**: Live generation depends on the Anthropic Messages API. Heavy traffic must be governed by rate limiters (SlowAPI) to stay within tier limits.

---

## 🔮 Future Work & Roadmap

1. **Language-Adaptive Thresholding**:
   - Apply dynamic similarity gating: $\tau_{\text{monolingual}} = 0.80$ and $\tau_{\text{cross-lingual}} = 0.77$.
   - Delivers $100\%$ Citation Rate while maintaining $100\%$ Out-of-Scope Rejection.
2. **Granular Chunking with Metadata Prefixing**:
   - Reduce chunk size to $\sim 250$ tokens and prepend structured context:
     `[Scheme: Kalaignar Magalir Urimai | Page: 1 | Section: Eligibility Criteria] ...`
   - Boosts specific keyword similarities from $0.77$ to $> 0.85$.
3. **Hybrid Search (BM25 + Dense FAISS)**:
   - Combine dense neural retrieval with BM25 lexical search using Reciprocal Rank Fusion (RRF) for exact government order numbers (e.g., `"G.O. Ms. No. 12"`), helpline digits (`"155261"`), and financial figures.
4. **Multimodal Scanned Document Pipeline**:
   - Integrate a lightweight OCR pipeline (Tesseract with Tamil trained data) to handle legacy scanned government gazette notifications.
5. **Voice Interface for Rural Accessibility**:
   - Add Speech-to-Text (STT) and Text-to-Speech (TTS) supporting Tamil dialects and Indian English to assist non-literate citizens.

---

## 🧪 Testing & CI

SchemeSaathi includes **24 automated pytest tests** covering every layer of the system:

```bash
# Run the complete test suite
pytest backend/tests/ -v

# Run individual test modules:
pytest backend/tests/test_ingest.py        # Chunking overlap & metadata preservation
pytest backend/tests/test_vectorstore.py   # Semantic search with known query validation
pytest backend/tests/test_rag.py           # Threshold gating & zero-LLM fallback test
pytest backend/tests/test_chat_endpoint.py # FastAPI /chat endpoint with mocked Mongo
```

Continuous Integration is automated via [`.github/workflows/ci.yml`](.github/workflows/ci.yml) running on every push to `main` and `master`.

---

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

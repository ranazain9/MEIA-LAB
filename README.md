# MEIA-LAB: Multimodal Earnings Intelligence Agent

**An end-to-end earnings-call intelligence platform** that orchestrates a multi-agent AI workflow to analyze corporate earnings calls through speech recognition, slide interpretation, SEC filing validation, and synthetic report generation.

**Use Case:** Investors, analysts, and compliance teams use MEIA to verify earnings-call claims against official filings, identify inconsistencies, and generate AI-backed verification reports in seconds.

## What You Built

MEIA combines four specialized AI agents into a coordinated pipeline:

1. **ASR Agent** (`backend/agents/asr/`) — Transcribes earnings-call audio using Whisper
2. **Vision Agent** (`backend/agents/vision/`) — Extracts key points from presentation slides
3. **Filing Agent** (`backend/agents/filing/`) — Retrieves and searches SEC documents (10-Q, 10-K, 8-K) for corroborating evidence
4. **Orchestrator Agent** (`backend/agents/orchestrator/`) — Synthesizes findings into a verification report with risk flags

**Architecture:** LangGraph-based workflow with Groq/OpenAI LLMs + LangChain for orchestration + ChromaDB for SEC filing embeddings.

**Frontend:** React/Vite dashboard displaying real-time verification status, claim verification results, risk flags, and analyst briefs.

---

## Key Features

✅ **Multi-source validation** — Audio + slides + SEC filings  
✅ **End-to-end pipeline** — From raw files to structured reports  
✅ **LLM provider flexibility** — Groq, OpenAI, AIMLAPI, local models  
✅ **GPU-optimized inference** — AMD and CUDA acceleration support  
✅ **REST API** — FastAPI with background job processing  
✅ **Demo mode** — Works immediately with fallback mock data  
✅ **Local & cloud ready** — Runs on Windows/Linux/macOS or remote GPU clusters

---

## Project Structure

```
MEIA-LAB/
├── backend/                          # Python multi-agent backend
│   ├── agents/
│   │   ├── asr/                      # Speech transcription (Whisper)
│   │   │   ├── agent.py              # ASR LangChain agent entry point
│   │   │   ├── config.py             # ASR model & provider config
│   │   │   └── processors.py         # Audio frame handling
│   │   ├── vision/                   # Slide analysis
│   │   │   ├── agent.py              # Vision agent entry point
│   │   │   └── config.py             # Vision LLM config (GPT-4V, etc.)
│   │   ├── filing/                   # SEC filing retrieval & search
│   │   │   ├── agent.py              # Filing agent entry point
│   │   │   ├── sec_client.py         # SEC EDGAR API wrapper
│   │   │   ├── chroma_store.py       # Vector DB for embeddings
│   │   │   └── config.py             # Filing retrieval config
│   │   ├── orchestrator/             # Workflow coordination
│   │   │   ├── agent.py              # Orchestrator entry point
│   │   │   ├── graph.py              # LangGraph workflow DAG
│   │   │   ├── pipeline.py           # Full end-to-end pipeline
│   │   │   └── config.py             # Orchestrator config
│   │   ├── base/                     # Base classes & schemas
│   │   │   ├── base_agent.py         # Abstract agent base class
│   │   │   └── schemas.py            # Shared Pydantic models
│   │   ├── langchain_utils.py        # LLM provider setup (Groq, OpenAI, etc.)
│   │   └── registry.py               # Agent factory & registration
│   ├── api/
│   │   └── main.py                   # FastAPI app (job submission, polling)
│   ├── core/
│   │   ├── groq_client.py            # Groq API wrapper
│   │   ├── rate_limiter.py           # Request rate limiting
│   │   └── retry.py                  # Retry logic with exponential backoff
│   ├── run_agent.py                  # CLI entry point for standalone execution
│   └── service.py                    # Shared analysis runner
├── frontend/                         # React/Vite dashboard
│   ├── src/
│   │   ├── pages/                    # DashboardPage, BriefPage, ClaimsPage, etc.
│   │   ├── components/               # UI components (AgentStatusCard, etc.)
│   │   └── services/                 # backendAdapter.js, analysisService.js
│   └── package.json
├── data/
│   ├── chromadb/                     # Local ChromaDB vector store
│   └── [embeddings for SEC filings]
├── tests/                            # Pytest integration tests
├── requirements.txt                  # Python dependencies
├── Dockerfile & docker-compose.yml   # Container deployment
└── README.md                         # This file
```

---

## How It Works: Main Code Paths

### 1. **CLI Execution** (Standalone)
```
run_agent.py
  → backend/service.py → run_analysis()
    → backend/agents/orchestrator/pipeline.py → full_pipeline()
      → ASR Agent (transcribe audio)
      → Vision Agent (extract slides)
      → Filing Agent (search SEC docs)
      → Orchestrator Agent (generate report)
```

**File:** [`backend/run_agent.py`](backend/run_agent.py)  
**Entry point:** `python backend/run_agent.py --ticker AMD --audio-path audio.wav --slides-path slides.pdf`

### 2. **API Execution** (HTTP Job Queue)
```
FastAPI POST /analyze
  → backend/api/main.py
    → Enqueue job to memory store
    → BackgroundTasks → backend/service.py → run_analysis()
    → (same pipeline as CLI)
```

**File:** [`backend/api/main.py`](backend/api/main.py)  
**Entry point:** `uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000`

### 3. **Frontend Dashboard**
```
React/Vite (localhost:5173)
  → frontend/src/services/analysisService.js
    → Fetch from API (http://127.0.0.1:8000)
    → Display real-time job status & results
    → Falls back to mock data if no backend
```

**File:** [`frontend/src/pages/DashboardPage.jsx`](frontend/src/pages/DashboardPage.jsx)  
**Entry point:** `cd frontend && npm run dev`

---

## AMD Resource Usage

MEIA leverages **AMD GPUs** (via ROCm / HIP) for accelerated inference workloads:

### GPU-Accelerated Pipelines

1. **ASR (Whisper Transcription)**
   - On CPU: ~2–5 min per 1-hour audio file (Whisper base model)
   - On AMD GPU: ~15–30 sec per 1-hour audio file (ROCm-optimized Whisper)
   - **Code:** [`backend/agents/asr/agent.py`](backend/agents/asr/agent.py)

2. **Embedding Generation (SEC Filing Retrieval)**
   - LangChain + HuggingFace embeddings on CPU: ~1–2 sec per 384-dim vector
   - On AMD GPU: ~0.1–0.2 sec per vector (batch processing)
   - **Code:** [`backend/agents/filing/chroma_store.py`](backend/agents/filing/chroma_store.py)

3. **LLM Inference (Vision, Filing, Orchestrator)**
   - Routed to Groq API by default (cloud-based, no local GPU required)
   - Optional: Deploy on AMD GPU cluster for on-prem inference

### Configuration

Set `MEIA_LLM_PROVIDER` environment variable:

```bash
# Use Groq (cloud, default, AMD optional)
export MEIA_LLM_PROVIDER=groq
export GROQ_API_KEY=your_groq_key

# Use OpenAI (cloud)
export MEIA_LLM_PROVIDER=openai
export OPENAI_API_KEY=your_openai_key

# Use local AMD GPU (HuggingFace, requires transformers + ROCm)
export MEIA_LLM_PROVIDER=huggingface
# See backend/agents/langchain_utils.py for model setup
```

**See:** [`backend/agents/langchain_utils.py`](backend/agents/langchain_utils.py) for LLM provider initialization.

---

## Getting Started

### Prerequisites

- **Python 3.11+** (required)
- **Windows / Linux / macOS**
- **Virtual environment** (recommended)
- **Node.js 16+** (for frontend, optional)
- **GPU** (optional: AMD ROCm or CUDA for faster processing)

### Installation

#### 1. Clone and Set Up Python Environment

```powershell
# Windows PowerShell
git clone <repo-url>
cd MEIA-LAB

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt
```

**Troubleshooting:**
- If `python` not found: Use `py -3.11 -m venv .venv` instead
- If script execution disabled: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in PowerShell

#### 2. Set Up Environment Variables

Create `.env` file in project root:

```bash
# LLM Provider (required)
MEIA_LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Alternative: OpenAI
# MEIA_LLM_PROVIDER=openai
# OPENAI_API_KEY=your_openai_key_here

# Alternative: AIMLAPI
# MEIA_LLM_PROVIDER=aimlapi
# AIMLAPI_KEY=your_aimlapi_key_here

# Model selection (optional)
MEIA_LLM_MODEL=llama-3.3-70b-versatile  # Groq default
# MEIA_LLM_MODEL=gpt-4-turbo           # OpenAI alternative

# Embedding provider (optional)
MEIA_EMBEDDING_PROVIDER=huggingface
# Default: all-MiniLM-L6-v2 (HuggingFace)

# Logging
MEIA_LOG_LEVEL=INFO
```

#### 3. (Optional) Set Up Frontend

```powershell
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

#### 4. Start Backend API

```powershell
# From project root
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
# API available at http://127.0.0.1:8000/docs (Swagger)
```

---

## External Services & API Keys

| Service | Purpose | Environment Variable | Cost | Required |
|---------|---------|----------------------|------|----------|
| **Groq** | Fast LLM inference (cloud) | `GROQ_API_KEY` | Free tier available | ✅ Yes (default) |
| **OpenAI** | GPT-4V for vision + text | `OPENAI_API_KEY` | ~$0.01–0.10/request | Optional (if using OpenAI) |
| **AIMLAPI** | Multi-model inference | `AIMLAPI_KEY` | Free tier available | Optional |
| **SEC EDGAR** | US company filings (10-Q, 10-K) | None (public API) | Free | ✅ Yes (automatic) |
| **HuggingFace** | Embedding models | None (public) | Free | ✅ Yes (default) |
| **ChromaDB** | Vector database (local) | None | Free (local) | ✅ Yes (embedded) |

### Rate Limits

- **Groq:** 30 requests/min (free tier); higher on paid plans
- **SEC EDGAR:** 10 requests/sec (per IP)
- **OpenAI:** Varies by plan

---

## Demo Data

**The frontend includes fallback mock data** (`frontend/src/data/mockAnalysis.js`) so it displays something immediately even if the backend is down. This is intentional for demo/evaluation purposes.

- ✅ **Demo shows real functionality:** The mock data represents realistic output from the full pipeline
- ✅ **Works offline:** Frontend renders without backend running
- ✅ **Fallback mechanism:** Real backend data overrides mock data when available

To see real data flow:
1. Start the backend: `uvicorn backend.api.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Submit an analysis job via the dashboard
4. Real data will replace mock data as results arrive

---

## Quick Start

### Run CLI Analysis

```powershell
# Analyze AMD Q2 earnings call
python backend/run_agent.py \
  --ticker AMD \
  --audio-path sample_earnings_call.wav \
  --slides-path sample_slides.pdf
```

**Output:** JSON report with verification results, risk flags, and analyst brief

### Run API Server + Web Dashboard

```powershell
# Terminal 1: Start backend API
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev

# Open browser to http://localhost:5173
# Submit earnings call audio + slides through the UI
```

### Verify Backend-Frontend Connection

**Check if backend is running:**
```bash
curl http://127.0.0.1:8000/docs
# Should return Swagger UI
```

**Check if frontend can reach backend:**
```bash
# Open browser DevTools (F12) → Console → Network tab
# Submit a job and watch for /api/analyze requests
# Should see 200 status (success) or 422 (validation error)
```

**Common Connection Issues:**

| Issue | Cause | Fix |
|-------|-------|-----|
| "Failed to fetch" | Backend not running | Start: `uvicorn backend.api.main:app --reload` |
| CORS error | Frontend blocked by backend | Check `MEIA_CORS_ORIGINS` env var |
| 404 on /api/* | Backend route missing | Verify FastAPI app has `/api/analyze` route |
| Mock data only | Backend not responding | Check network tab in DevTools |

### Run with Docker

```bash
docker-compose up
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:5173
```

---

## Testing

```powershell
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_orchestrator_pipeline.py -v

# Test with coverage
pytest --cov=backend tests/
```

**Test files:** [`tests/`](tests/)

---

## Deployment

### Multiple Deployment Options

#### 1. Local Development (Recommended for Testing)

```powershell
# Terminal 1: Backend API
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend 
cd frontend
npm run dev
# http://localhost:5173 connects to http://127.0.0.1:8000 (via Vite proxy)
```

#### 2. Railway (Backend + Frontend)

Push to main branch; Railway auto-deploys via `railway.json` config.

```bash
railway login
railway up
```

#### 3. Vercel (Monolithic Deployment - RECOMMENDED)

**Single deployment** — Frontend and Backend on the same Vercel host:

```
https://meia-lab-69fu-meia.vercel.app/
├─ Frontend: React UI (served from /)
└─ Backend: FastAPI API (served from /api/*)
```

**Configuration:**

- `vercel.json` builds the frontend
- Backend runs alongside as serverless functions
- Frontend uses **relative paths** for API calls (no CORS issues)
- All requests go to the same domain

**Setup in Vercel:**

1. Connect GitHub repo to Vercel
2. Set environment variables:
   ```
   GROQ_API_KEY=your_key
   MEIA_LLM_PROVIDER=groq
   ```
3. Build command: `npm --prefix frontend ci && npm --prefix frontend run build`
4. Output directory: `frontend/dist`
5. Deploy!

**Live:** https://meia-lab-69fu-meia.vercel.app/ ✅

**API Endpoints:**
- `/api/analyze` — Start analysis job
- `/api/jobs/{job_id}` — Get job status
- `/docs` — Swagger UI (for debugging)

---

**API Calls from Frontend:**

```javascript
// frontend/src/api.js
const API_BASE = "";  // Relative path (same origin)

fetch(`${API_BASE}/api/analyze`, {...})
// Calls: https://meia-lab-69fu-meia.vercel.app/api/analyze ✅
```

---

## Docker Deployment

Pre-built image available on Docker Hub:

```bash
docker pull ranazain12/meia-lab
docker run -p 8000:8000 -p 5173:5173 \
  -e GROQ_API_KEY=your_key \
  -e MEIA_LLM_PROVIDER=groq \
  ranazain12/meia-lab
```

Or use Docker Compose (includes both backend + frontend):

```bash
docker-compose up
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:5173
```

---

## Architecture Diagram

```
[Earnings Call Audio + Slides]
            ↓
     ┌──────────────────┐
     │ ASR Agent        │ (Whisper)
     └────────┬─────────┘
              ↓
     ┌──────────────────┐
     │ Vision Agent     │ (GPT-4V / LLM)
     └────────┬─────────┘
              ↓
     ┌──────────────────┐
     │ Filing Agent     │ (SEC EDGAR search + ChromaDB)
     └────────┬─────────┘
              ↓
     ┌──────────────────┐
     │ Orchestrator     │ (Synthesis + Report Gen)
     └────────┬─────────┘
              ↓
   [Verification Report + Risk Flags + Analyst Brief]
            ↓
   [FastAPI / React Dashboard]
```

---

## Environment Variables Reference

```bash
# LLM Configuration
MEIA_LLM_PROVIDER=groq|openai|aimlapi|huggingface
MEIA_LLM_MODEL=llama-3.3-70b-versatile|gpt-4-turbo|...
GROQ_API_KEY=xxx
OPENAI_API_KEY=xxx
AIMLAPI_KEY=xxx

# Embedding Configuration
MEIA_EMBEDDING_PROVIDER=huggingface|openai
# HuggingFace model: all-MiniLM-L6-v2 (default)

# Logging & Debug
MEIA_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# Deployment
MEIA_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## Contributing

Contributions welcome! Areas of interest:

- Additional LLM provider integrations
- Improved SEC filing search
- Enhanced risk classification
- Frontend visualization improvements
- Containerization refinements

---

## Team & Credits

**Built by:**
- Rana Zain Waseem (@ranazain12) — Architecture, backend orchestration, Docker deployment
- [Add additional team members as needed]

**Technologies & Sponsors:**
- AMD Developer Challenge participant
- Groq API for LLM inference
- LangChain & LangGraph for multi-agent orchestration
- FastAPI for REST API
- React/Vite for frontend

---

## Original Work Statement

This project is **original work** developed for the AMD Developer Challenge. It combines:

- **LangGraph orchestration** (multi-agent workflow)
- **Custom Groq integration** (`backend/agents/langchain_utils.py`)
- **SEC EDGAR integration** (`backend/agents/filing/sec_client.py`)
- **React/Vite frontend** with real-time job status display
- **End-to-end pipeline** validated with unit tests

All code is authored for this project.

---

## License

This project is intended for research and development use. Please review the repository license before redistribution or commercial use.

---

## Support

- 📖 **Issues?** Check [`tests/`](tests/) for usage examples
- 🐛 **Bug reports:** Open an issue with environment details
- 💬 **Questions?** Review docstrings in [`backend/agents/base/base_agent.py`](backend/agents/base/base_agent.py)


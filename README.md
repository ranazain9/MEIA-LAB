# MEIA-LAB

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](#getting-started)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](#architecture)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-646CFF)](#architecture)
[![Testing](https://img.shields.io/badge/tests-pytest%20%2B%20unittest-informational)](#testing)
[![License](https://img.shields.io/badge/license-R%26D-lightgrey)](#license)

MEIA-LAB is a multi-agent earnings-call intelligence platform that cross-checks management commentary against slides and SEC filings to produce evidence-backed analyst insights.

## Focus

- **Role**: AI-assisted financial research workflow
- **Specialization**: multi-agent orchestration (ASR, vision, filing retrieval, synthesis)
- **Current focus**: improving reliability, claim-verification accuracy, and production readiness

## Why MEIA-LAB

Manual earnings-call review is slow and error-prone. MEIA-LAB reduces analysis time by combining:

1. speech transcription from call audio,
2. slide understanding from presentation decks,
3. filing retrieval and claim validation from SEC sources,
4. unified synthesis into dashboard metrics and briefs.

## Architecture

```text
backend/
  agents/
    asr/           # Speech transcription and speaker-level analysis
    vision/        # Slide extraction and semantic understanding
    filing/        # SEC retrieval, chunking, and claim verification
    orchestrator/  # Final synthesis and report generation
  api/             # FastAPI endpoints for job execution and polling
  service.py       # Shared end-to-end analysis runner

frontend/
  src/pages/       # Dashboard, evidence room, analyst brief, processing views
  src/services/    # API adapters and analysis normalization
```

## Product Flow

1. Upload ticker + audio + slides
2. Run asynchronous analysis job
3. Inspect dashboard health metrics and risk flags
4. Review claim-level evidence and consistency outcomes
5. Export analyst-oriented brief

## Demos and Supporting Material

- Hackathon demo script and submission content: [`docs/hackathon_submission_materials.md`](docs/hackathon_submission_materials.md)
- API-first local run path: [`backend/api/main.py`](backend/api/main.py)
- End-to-end runner: [`backend/run_agent.py`](backend/run_agent.py)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Virtual environment tooling

### Backend setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run backend API

```bash
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend setup and run

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# backend
python -m pytest
python -m unittest discover -s tests

# frontend (production build smoke test)
cd frontend && npm run build
```

## Evidence and Result Signals

The platform is designed to surface measurable output signals such as:

- claim consistency score,
- verified vs. unsupported claims,
- risk-factor extraction,
- source-linked evidence snippets,
- generated analyst brief quality.

## Roadmap

- [ ] Add explicit CI workflows for backend tests and frontend build checks
- [ ] Expand contract tests between backend outputs and frontend adapters
- [ ] Improve filing failure visibility (separate "no data" vs "retrieval error")
- [ ] Harden model/provider configuration for local and cloud environments
- [ ] Add benchmark tracking for latency and verification precision

## What We Are Working On Now

- Stabilizing environment setup across Windows/Linux/macOS
- Improving reliability of ASR and filing-agent initialization paths
- Aligning backend output contracts with dashboard/evidence views

## Team

- **Rana zain (ME) ** — **AI Engineer, Team Lead**
- **Rimsha Talib** (@rimshatalib) — **Frontend**
- **Vaibhav** (@vaibhavcs99) — **Frontend**
- **Akhil Nirala** (@akhilnirala01-dotcom) — **UI/UX**
- **Linta Habib** (@lintahabib2-hash) — **Presentation & Deployment**
- **Leston Osoi** (@lestonEth) — **Backend Developer**

## Open to Collaboration

We welcome collaborators on:

- agent reliability and observability,
- financial claim-verification quality,
- frontend UX for evidence-driven analyst workflows.

Open an issue or submit a pull request with your proposal.

## License

This project is intended for research and development use. Review the repository license before redistribution or commercial use.

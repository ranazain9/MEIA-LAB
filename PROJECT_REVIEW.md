# MEIA-LAB Project Review

Review date: 2026-07-09

## Summary

The project is a full-stack earnings-call intelligence prototype with a FastAPI backend, multi-agent Python pipeline, and Vite/React frontend. The architecture is understandable and the repo has useful unit tests, but the current checkout has several setup and build problems that block reliable local validation.

## Confirmed Errors

### 1. Frontend production build fails

Command:

```powershell
cd frontend
npm.cmd run build
```

Result:

```text
[plugin vite:build-html]
Error: The "fileName" or "name" properties of emitted chunks and assets must be strings that are neither absolute nor relative paths, received "D:/MEIA-LAB/frontend/index.html".
```

Relevant files:

- `frontend/package.json:19`
- `frontend/package-lock.json`

Likely cause:

`frontend/package.json` currently uses `vite` `^8.1.3`. The lockfile shows this moved the project from Vite 5/Rollup to Vite 8/Rolldown. The installed Vite/Rolldown path is failing during HTML emission on Windows.

Recommended fix:

Pin Vite back to the previously working stable line, for example `^5.4.2` or a known compatible Vite 5 patch version, then reinstall frontend dependencies and rebuild. Also avoid committing broad lockfile churn unless the dependency upgrade is intentional and verified.

### 2. PowerShell cannot run `npm` directly

Command:

```powershell
npm run build
```

Result:

```text
npm.ps1 cannot be loaded because running scripts is disabled on this system.
```

Relevant files:

- No project file directly causes this.

Cause:

This is a Windows PowerShell execution policy issue. It is not a project code bug.

Recommended workaround:

Use `npm.cmd run build` in PowerShell, or run the command from `cmd.exe` / another shell.

### 3. Python command and virtual environment are broken in this environment

Commands:

```powershell
python -m pytest
py -m pytest
.\.venv\Scripts\python.exe -m pytest
```

Results:

```text
python: The term 'python' is not recognized
py: The term 'py' is not recognized
did not find executable at ... WindowsApps\PythonSoftwareFoundation.Python.3.13...\python.exe: Access is denied.
```

Relevant files:

- `README.md:46`
- `README.md:54`
- `.venv/`

Cause:

The local Python launcher is unavailable, and `.venv` appears to reference an inaccessible Windows Store Python shim.

Recommended fix:

Recreate the virtual environment with a real Python 3.11+ installation:

```powershell
Remove-Item -Recurse -Force .venv
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

If `py` is not available, install Python from python.org and ensure it is added to `PATH`.

### 4. Unit tests cannot pass without installed backend dependencies

Command:

```powershell
python -m unittest discover -s tests
```

Using a clean bundled Python interpreter, the suite ran but failed because project dependencies were not installed:

```text
ModuleNotFoundError: No module named 'bs4'
Failed to fetch SEC filings: No module named 'httpx'
```

Relevant files:

- `backend/agents/filing/sec_client.py:80`
- `backend/agents/filing/processors.py:95`
- `requirements.txt:22`
- `requirements.txt:23`
- `tests/test_sec_client.py:23`
- `tests/test_sec_client.py:66`

Cause:

`httpx` and `beautifulsoup4` are correctly listed in `requirements.txt`, but the active Python environment did not have them installed.

Recommended fix:

After recreating `.venv`, run:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

## Code Risks And Bugs

### 1. Filing failures can be silently downgraded to empty results

Relevant file:

- `backend/agents/filing/processors.py:84`
- `backend/agents/filing/processors.py:145`

Issue:

`fetch_sec_filings` catches broad exceptions, logs `Failed to fetch SEC filings`, and returns an empty list. This means missing dependencies, network failures, SEC API errors, or parser bugs can look like "no filings available" to the rest of the pipeline.

Impact:

The dashboard/report may show reduced verification or fallback data instead of surfacing a real backend failure.

Recommended fix:

Return a structured error object, add an error field to the filing agent output, or re-raise critical setup errors such as missing `httpx`. At minimum, distinguish "no filings found" from "filing retrieval failed".

### 1a. Runtime job failure: ASR and Filing model initialization

Observed log:

```text
POST /api/analyze HTTP/1.1" 200 OK
Failed to initialize Transformers ASR pipeline
OSError: The paging file is too small for this operation to complete. (os error 1455)
Failed to initialize agent filing_crosscheck
RuntimeError: Could not load libtorchcodec
Job ... failed
GET /api/jobs/... HTTP/1.1" 200 OK
```

Relevant files:

- `backend/agents/asr/processors.py`
- `backend/agents/asr/config.py`
- `backend/agents/filing/agent.py`
- `backend/agents/filing/config.py`
- `backend/agents/langchain_utils.py`
- `backend/agents/registry.py`

Issue:

The request itself succeeds because `/api/analyze` only starts a background job. The job later fails during agent initialization. There are two separate runtime blockers:

1. `openai/whisper-large-v3` is too heavy for the current Windows environment and fails while loading with `os error 1455`, meaning the paging file/virtual memory is too small.
2. The Filing agent initializes HuggingFace sentence-transformer embeddings, which imports `torchcodec`. `torchcodec` then fails because FFmpeg/full shared DLLs and/or the installed PyTorch/TorchCodec versions are incompatible.

Impact:

The backend returns `200 OK` for job creation, but the actual analysis job fails. The frontend can poll the job successfully, but it will receive a failed job instead of dashboard-ready analysis output.

Fastest local workaround:

- Use a smaller ASR model such as `small` or `base` instead of `large-v3`.
- Set the Filing embedding provider to `local` for smoke tests so it uses `SimpleLangChainEmbeddings` and bypasses `sentence_transformers`/`torchcodec`.

Example intended config:

```powershell
MEIA_EMBEDDING_PROVIDER=local
```

Code-level fixes:

- Add environment-variable support for ASR model selection, or pass agent configs from `run_analysis`, so users do not need to edit Python files to switch from `large-v3` to `small`.
- Add real `openai` embedding support in `build_embeddings` so cloud embeddings can replace local sentence-transformer embeddings.
- Consider making `registry.initialize_all()` tolerant of optional agent failures, returning partial output instead of failing the whole job when ASR or Filing cannot initialize.
- Pin compatible `torch`, `sentence-transformers`, and `torchcodec` versions, or avoid importing `torchcodec` through the embedding path.
- If using local audio/media packages on Windows, install FFmpeg full shared builds and ensure the DLL directory is on `PATH`.

### 2. ASR alignment is advertised but not implemented

Relevant files:

- `README.md:9`
- `README.md:27`
- `backend/agents/asr/processors.py:189`
- `backend/agents/asr/processors.py:195`

Issue:

The README describes speech transcription and alignment, but `align_transcript` still contains `TODO: Implement alignment`.

Impact:

Users may expect word-level or forced alignment quality that the code does not yet provide.

Recommended fix:

Either implement the alignment step or update the README/API wording to describe the current behavior accurately.

### 3. Frontend contains mojibake text

Relevant files:

- `frontend/src/data/mockAnalysis.js`
- `frontend/src/pages/ProcessingPage.jsx`
- `frontend/src/services/backendAdapter.js`

Examples seen:

```text
corrupted middle-dot separators
corrupted em-dash separators
corrupted minus signs
```

Issue:

Some display strings appear to have been saved with the wrong encoding.

Impact:

The UI will show corrupted separators/dashes in cards, agent messages, report citations, and job status text.

Recommended fix:

Replace corrupted sequences with plain ASCII equivalents, such as `-`, `->`, `/`, or normal spaces. Then ensure the files are saved as UTF-8.

### 4. Mock dashboard data is hard-coded as AMD Q2 2026

Relevant file:

- `frontend/src/data/mockAnalysis.js`

Issue:

The fallback data presents realistic-looking AMD Q2 2026 claims, financial values, SEC references, and transcript lines. This is useful for a demo, but it may be mistaken for real analysis output.

Impact:

If backend processing fails or returns partial data, users may see polished mock results and assume they are real.

Recommended fix:

Make fallback/demo mode visually explicit in the UI and avoid highly specific financial claims unless they are clearly labeled as sample data.

### 5. Frontend snapshot metadata was not shared across pages

Relevant files:

- `frontend/src/services/backendAdapter.js`
- `frontend/src/services/analysisService.js`
- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/pages/BriefPage.jsx`
- `frontend/src/pages/EvidencePage.jsx`
- `frontend/src/pages/ProcessingPage.jsx`

Issue:

The dashboard, brief, evidence room, and processing screen each hardcoded their own version of the same demo context. That caused date and period labels to drift, even when the actual analysis payload was consistent.

Impact:

The UI looked like multiple different demos glued together instead of one analysis snapshot flowing through the app.

Recommended fix:

Keep company, period, and generated timestamp in a shared analysis snapshot and render those values from the same service layer everywhere. That is now the pattern in the frontend.

## Verification Performed

Commands attempted:

```powershell
npm run build
npm.cmd run build
python -m pytest
py -m pytest
.\.venv\Scripts\python.exe -m pytest
python -m unittest discover -s tests
```

What worked:

- `npm.cmd run build` executed Vite and exposed the real frontend build failure.
- `npm.cmd run build` now passes after the frontend snapshot and label sync changes.
- `unittest discover` executed 11 tests with the bundled Python interpreter, but failed due to missing backend dependencies in that interpreter.

What did not work:

- `npm run build` was blocked by PowerShell execution policy.
- `python`, `py`, and the project `.venv` Python were unavailable/broken in this environment.

## Suggested Models

Note:

The project currently supports `MEIA_LLM_PROVIDER`, `MEIA_LLM_MODEL`, and `MEIA_EMBEDDING_PROVIDER`. I attempted to verify the latest OpenAI model guide online, but the official docs endpoint was not reachable from this environment. The recommendations below use the local OpenAI docs fallback bundled with Codex and should be rechecked before production deployment.

### Recommended default setup

Use this for best quality during demos and report generation:

```powershell
MEIA_LLM_PROVIDER=openai
MEIA_LLM_MODEL=gpt-5.5
MEIA_EMBEDDING_PROVIDER=openai
MEIA_EMBEDDING_MODEL=text-embedding-3-large
```

Why:

- `gpt-5.5` is the recommended general reasoning/synthesis model in the bundled guide.
- `text-embedding-3-large` is the higher-quality retrieval embedding choice.
- This setup should improve executive summaries, risk descriptions, filing claim interpretation, and final brief quality.

### Lower-cost development setup

Use this while iterating locally:

```powershell
MEIA_LLM_PROVIDER=openai
MEIA_LLM_MODEL=gpt-5.4-mini
MEIA_EMBEDDING_PROVIDER=openai
MEIA_EMBEDDING_MODEL=text-embedding-3-small
```

Why:

- Good enough for adapter and dashboard tests.
- Lower cost and latency than the highest-quality setup.

### Local/GPU-heavy setup

Current defaults are reasonable for local experimentation:

- ASR: `openai/whisper-large-v3`, configured through `backend/agents/asr/config.py`.
- Vision: `Qwen/Qwen2.5-VL-7B-Instruct`, configured through `backend/agents/vision/config.py`.
- Filing embeddings: `BAAI/bge-base-en-v1.5`, configured through `backend/agents/filing/config.py`.

Recommended adjustment:

Use GPU only where it gives clear benefit. ASR and vision are the best GPU candidates. Filing retrieval and orchestration are more sensitive to network/API reliability and structured output quality.

### Cloud embeddings instead of local embeddings

Recommendation:

Use cloud embeddings for the Filing agent if the goal is reliable dashboard-quality evidence matching. Local embeddings are fine for offline demos, but cloud embeddings reduce setup friction and make SEC filing retrieval more consistent across machines.

Suggested cloud embedding setup:

```powershell
MEIA_EMBEDDING_PROVIDER=openai
MEIA_EMBEDDING_MODEL=text-embedding-3-large
```

Lower-cost option:

```powershell
MEIA_EMBEDDING_PROVIDER=openai
MEIA_EMBEDDING_MODEL=text-embedding-3-small
```

Current code caveat:

`backend/agents/filing/config.py` currently documents only `hf/local`, and `backend/agents/langchain_utils.py` currently builds HuggingFace embeddings or a simple local fallback. To truly use OpenAI cloud embeddings, add an `openai` branch in `build_embeddings`, for example using LangChain's OpenAI embeddings integration, and pass the configured embedding model from environment/config.

Why cloud embeddings help here:

- Filing evidence retrieval becomes less dependent on local GPU/CPU setup.
- The same SEC filing chunks should retrieve more consistently across developer machines.
- The frontend evidence table depends on `verification_results`, so better retrieval directly improves dashboard output.

Tradeoffs:

- Requires an API key and network access.
- Adds per-run cost.
- SEC filing text may contain sensitive analysis context, so confirm data-handling expectations before production use.

### Agents that use LLMs for reasoning

From the current backend code, 2 of the 4 main agents use an LLM/VLM for reasoning or generation:

1. `VisionAgent` uses `build_llm` and calls the model during slide analysis.
   - Files: `backend/agents/vision/agent.py`, `backend/agents/vision/processors.py`
   - Purpose: slide understanding, KPI extraction, charts, tables, guidance.

2. `OrchestratorAgent` uses `build_llm` for executive summary generation and optional risk detection.
   - Files: `backend/agents/orchestrator/agent.py`, `backend/agents/orchestrator/processors.py`
   - Purpose: synthesis, report generation, risk/anomaly detection.

The other two main agents do not use an LLM for reasoning:

- `ASRAgent` uses a Whisper/Hugging Face speech pipeline for transcription, diarization, tone, and alignment support.
- `FilingAgent` uses SEC retrieval, embeddings, Chroma vector search, and rule/numeric verification. It uses embedding models, but not an LLM.

## Agent Output Tests For Frontend Dashboard

The frontend does not consume raw agent internals directly. It maps the backend job response through `frontend/src/services/backendAdapter.js`, which expects this shape:

```text
job.result.data.executive_summary
job.result.data.consistency_score
job.result.data.risk_factors
job.result.data.slide_speech_comparison
job.result.data.verification_results
job.result.data.tone_analysis.segments
job.status
job.ticker
job.completed_at
```

### Add a frontend adapter contract test

Create tests for `normalizeJobToAnalysis` with a fake completed backend job. The test should assert:

- Dashboard summary uses `executive_summary`.
- Consistency metric uses `consistency_score`.
- Risk monitor uses `risk_factors`.
- Evidence page uses `verification_results` when present.
- Evidence falls back to `slide_speech_comparison` when no filing verification exists.
- Agent status cards show ASR, Vision, Filing, and Orchestrator as active when matching backend fields exist.
- Quality card counts claims from comparisons plus verifications.

Minimum fixture:

```js
const job = {
  job_id: "job-123456",
  status: "completed",
  ticker: "AMD",
  completed_at: "2026-07-09T10:00:00Z",
  result: {
    data: {
      executive_summary: "AMD call summary from backend.",
      consistency_score: 0.91,
      tone_analysis: {
        speaker_count: 2,
        segments: [{ speaker: "CEO", confidence: 0.88 }],
      },
      risk_factors: [
        { label: "Guidance mismatch", severity: "high", description: "Revenue claim needs review." },
      ],
      slide_speech_comparison: [
        { slide_metric: "Revenue=12%", speech_reference: "Revenue grew 12%.", status: "reviewed" },
      ],
      verification_results: [
        {
          claim_text: "Revenue grew 12%",
          claimed_value: "12%",
          is_consistent: true,
          confidence: 0.93,
          source_filing: "amd-10q.htm",
          evidence_snippet: "Revenue increased 12%.",
        },
      ],
      full_report: "# AMD Analyst Intelligence Brief\n\nBackend report body.",
    },
  },
};
```

### Add an orchestrator output contract test

Extend `tests/test_orchestrator_report.py` so `_generate_report` asserts that all frontend-required fields are present:

```text
executive_summary
tone_analysis
consistency_score
risk_factors
slide_speech_comparison
historical_comparison
full_report
verification_results
```

Important bug to check:

`backend/agents/orchestrator/agent.py` builds `verification_results` inside `_generate_report`, but `_process_impl` currently returns only selected fields in `AgentOutput.data`. Ensure `verification_results` is included in the final API result, otherwise the frontend evidence page will not receive filing evidence and will fall back to less useful comparison data.

### Add one end-to-end mocked API test

Mock ASR, Vision, and Filing agent outputs, run `run_analysis`, then pass the returned job-like object into `normalizeJobToAnalysis`. The expected final object should contain:

- `dashboard.summary`
- `dashboard.metrics`
- `risks`
- `evidence`
- `brief.sections`
- `agents`
- `quality.stats`

This is the best test for the user-facing flow because it catches backend/frontend field drift before it reaches the UI.

## Suggested Priority Order

1. Fix frontend dependency/build issue by reverting or pinning Vite to a known working version.
2. Recreate the Python virtual environment and install `requirements.txt`.
3. Run the full Python test suite with `pytest`.
4. Fix mojibake display strings in frontend files.
5. Improve filing error propagation so backend failures are visible.
6. Implement ASR alignment or update the documentation to avoid overpromising.
7. Add frontend adapter and orchestrator contract tests for dashboard output.

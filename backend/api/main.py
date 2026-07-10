"""
MEIA FastAPI Server
===================

REST API for earnings call analysis with background job tracking.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.service import run_analysis

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("MEIA_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="MEIA API",
    description="Multimodal Earnings Intelligence Agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("MEIA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: Dict[str, Dict[str, Any]] = {}


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str = ""


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    current_step: str = ""
    ticker: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


async def _run_job(job_id: str, audio_path: str, slides_path: str, ticker: str) -> None:
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["current_step"] = "starting"
    logger.info("Job %s started for %s", job_id, ticker)
    try:
        _jobs[job_id]["current_step"] = "analysis"
        result = await run_analysis(audio_path, slides_path, ticker)
        logger.info(
            "Orchestrator returned for job %s; result keys=%s",
            job_id,
            list(result.keys()) if isinstance(result, dict) else type(result).__name__,
        )
        _jobs[job_id]["result"] = result
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _jobs[job_id]["current_step"] = "finished"
        logger.info(
            "Result stored for job %s (ticker=%s), current_step=finished",
            job_id,
            ticker,
        )
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _jobs[job_id]["current_step"] = "failed"
    finally:
        temp_root = _jobs[job_id].get("temp_dir")
        if temp_root:
            shutil.rmtree(temp_root, ignore_errors=True)


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "meia"}


@app.post("/api/analyze", response_model=JobResponse)
async def analyze(
    background_tasks: BackgroundTasks,
    ticker: str = Form(..., min_length=1, max_length=10),
    audio: UploadFile = File(...),
    slides: UploadFile = File(...),
) -> JobResponse:
    """Upload earnings call assets and start background analysis."""
    ticker = ticker.strip().upper()
    if not audio.filename or not slides.filename:
        raise HTTPException(status_code=400, detail="Both audio and slides files are required.")

    job_id = str(uuid4())
    temp_dir = Path(tempfile.mkdtemp(prefix=f"meia_{job_id}_"))
    audio_suffix = Path(audio.filename).suffix or ".wav"
    slides_suffix = Path(slides.filename).suffix or ".pdf"
    audio_path = temp_dir / f"audio{audio_suffix}"
    slides_path = temp_dir / f"slides{slides_suffix}"

    await _save_upload(audio, audio_path)
    await _save_upload(slides, slides_path)

    _jobs[job_id] = {
        "status": "pending",
        "ticker": ticker,
        "current_step": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "temp_dir": str(temp_dir),
        "result": None,
        "error": None,
        "completed_at": None,
    }

    background_tasks.add_task(
        _run_job,
        job_id,
        str(audio_path),
        str(slides_path),
        ticker,
    )

    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Analysis started for {ticker}.",
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str) -> JobStatusResponse:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    result = job.get("result")
    if job["status"] == "completed" and result is not None:
        logger.info(
            "API returning result for job %s, result keys=%s",
            job_id,
            list(result.keys()) if isinstance(result, dict) else type(result).__name__,
        )

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        current_step=job.get("current_step", ""),
        ticker=job.get("ticker", ""),
        created_at=job.get("created_at", ""),
        completed_at=job.get("completed_at"),
        error=job.get("error"),
        result=result,
    )


FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

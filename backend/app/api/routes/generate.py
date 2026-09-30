import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.db.connection import get_db
from app.db import jobs_repo, sessions_repo
from app.core.job_runner import run_job
from app.schemas.jobs import JobResponse

router = APIRouter(prefix="/api/generate", tags=["generate"])


@router.post("/{session_id}/{template_id}", response_model=JobResponse)
def generate(
    session_id: str,
    template_id: str,
    background_tasks: BackgroundTasks,
    db: DBSession = Depends(get_db),
):
    """
    Starts document generation for a given template.
    Runs in the background; poll /status/{job_id} for progress.
    Session must be in 'confirmed' status.
    """
    session = sessions_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "confirmed":
        raise HTTPException(status_code=400, detail="Session must be confirmed before generating.")

    job_id     = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    job        = jobs_repo.create_job(db, job_id, session_id, template_id, created_at)

    background_tasks.add_task(run_job, db, job_id, session_id, template_id)
    return job


@router.get("/status/{job_id}", response_model=JobResponse)
def job_status(job_id: str, db: DBSession = Depends(get_db)):
    """Returns the current status and output path of a generation job."""
    job = jobs_repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

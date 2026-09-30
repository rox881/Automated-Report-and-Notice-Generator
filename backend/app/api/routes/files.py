from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from app.db.connection import get_db
from app.db import jobs_repo

router = APIRouter(prefix="/api/download", tags=["files"])


@router.get("/{job_id}")
def download(job_id: str, db: DBSession = Depends(get_db)):
    """Streams the generated .docx file to the browser as a download."""
    job = jobs_repo.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done":
        raise HTTPException(status_code=400, detail=f"Job is '{job.status}', not ready yet.")

    path = Path(job.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file missing on disk.")

    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )

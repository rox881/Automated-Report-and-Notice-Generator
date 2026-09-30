from datetime import datetime, timezone
from sqlalchemy.orm import Session as DBSession

from app.db import jobs_repo, sessions_repo
from app.registry.loader import get_fields
from app.core.formatter import build_context
from app.core.filler import fill_template
from app.storage.file_store import get_output_path


def run_job(db: DBSession, job_id: str, session_id: str, template_id: str):
    """
    Executes a single document generation job.
    Transitions: pending → running → done | failed
    """
    jobs_repo.update_job(db, job_id, status="running")

    try:
        values  = sessions_repo.get_field_values(db, session_id)
        fields  = get_fields(template_id)
        context = build_context(fields, values)

        output_path = get_output_path(session_id, template_id)
        fill_template(template_id, context, output_path)

        finished = datetime.now(timezone.utc).isoformat()
        jobs_repo.update_job(
            db, job_id,
            status="done",
            output_path=output_path,
            finished_at=finished,
        )

    except Exception as e:
        finished = datetime.now(timezone.utc).isoformat()
        jobs_repo.update_job(
            db, job_id,
            status="failed",
            error=str(e),
            finished_at=finished,
        )
        raise

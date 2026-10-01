from datetime import datetime, timezone

from app.db import jobs_repo, sessions_repo
from app.registry.loader import get_fields
from app.core.formatter import build_context
from app.core.filler import fill_template
from app.storage.file_store import get_output_path


def run_job(SessionLocal, job_id: str, session_id: str, template_id: str):
    """
    Executes a single document generation job in a background thread.
    Opens its OWN fresh DB session via SessionLocal() — never reuses the
    request-scoped session that gets closed when the HTTP response is sent.
    Transitions: pending → running → done | failed
    """
    db = SessionLocal()
    try:
        jobs_repo.update_job(db, job_id, status="running")

        # Fresh read — guaranteed to see all committed field values
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

    finally:
        db.close()  # Always close the session we opened

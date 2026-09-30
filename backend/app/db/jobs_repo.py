from sqlalchemy.orm import Session as DBSession
from app.db.models import Job


def create_job(db: DBSession, job_id: str, session_id: str, template_id: str, created_at: str) -> Job:
    job = Job(id=job_id, session_id=session_id, template_id=template_id, status="pending", created_at=created_at)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: DBSession, job_id: str) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()


def get_jobs_for_session(db: DBSession, session_id: str) -> list[Job]:
    return db.query(Job).filter(Job.session_id == session_id).all()


def update_job(db: DBSession, job_id: str, **kwargs):
    db.query(Job).filter(Job.id == job_id).update(kwargs)
    db.commit()

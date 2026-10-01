import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.db.connection import get_db
from app.db import sessions_repo
from app.schemas.session import SessionCreate, SessionResponse
from app.core.extractor import extract_fields
from app.core.gap_checker import find_missing
from app.registry.loader import get_fields

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session(body: SessionCreate, db: DBSession = Depends(get_db)):
    """Creates a new session with the pasted context text."""
    session_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    return sessions_repo.create_session(db, session_id, body.context, created_at)


@router.post("/{session_id}/extract")
def extract(session_id: str, template_id: str, db: DBSession = Depends(get_db)):
    """
    Runs LLM extraction for a given template and saves field values.
    Supports two-phase flow: if session is already 'confirmed' (notice done),
    extracting for report does NOT downgrade the session status.
    Returns status and list of missing fields with required flag.
    """
    session = sessions_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    extracted = extract_fields(template_id, session.context)
    sessions_repo.save_field_values(db, session_id, extracted, source="llm")

    fields  = get_fields(template_id)
    missing = find_missing(fields, extracted)
    field_map = {f.key: f for f in fields}

    missing_response = [
        {
            "key": m.key,
            "label": m.label,
            "type": m.type,
            "required": field_map[m.key].required,
        }
        for m in missing
        if m.key in field_map
    ]

    has_required_missing = any(m["required"] for m in missing_response)
    new_status = "needs_input" if has_required_missing else "extracted"

    # KEY FIX: Never downgrade a confirmed session.
    # If the session is already confirmed (notice done), keep it confirmed
    # so the generate endpoint does not block report generation.
    if session.status != "confirmed":
        sessions_repo.update_status(db, session_id, new_status)

    return {
        "status": session.status if session.status == "confirmed" else new_status,
        "missing": missing_response,
    }


@router.get("/{session_id}/preview")
def preview(session_id: str, template_id: str, db: DBSession = Depends(get_db)):
    """Returns all field values for user review and inline editing."""
    fields = get_fields(template_id)
    values = sessions_repo.get_field_values(db, session_id)

    return [
        {
            "key": spec.key,
            "label": spec.label,
            "value": values.get(spec.key),
            "source": "llm",
            "required": spec.required,
        }
        for spec in fields
    ]


@router.get("")
def list_sessions(db: DBSession = Depends(get_db)):
    """Returns all past sessions for the sidebar history with event title."""
    sessions = sessions_repo.get_all_sessions(db)
    result = []
    for s in sessions:
        values = sessions_repo.get_field_values(db, s.id)
        event_title = (
            values.get("event_title")
            or values.get("session_title")
            or "Untitled"
        )
        result.append({
            "id": s.id,
            "status": s.status,
            "created_at": s.created_at,
            "event_title": event_title,
        })
    return result

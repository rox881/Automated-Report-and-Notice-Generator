from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.db.connection import get_db
from app.db import sessions_repo
from app.schemas.fields import UserAnswers
from app.core.gap_checker import find_missing, find_missing_required
from app.registry.loader import get_fields

router = APIRouter(prefix="/api/fields", tags=["fields"])


@router.get("/{session_id}/missing")
def get_missing(session_id: str, template_id: str, db: DBSession = Depends(get_db)):
    """Returns all fields with empty values, with required flag attached."""
    fields   = get_fields(template_id)
    values   = sessions_repo.get_field_values(db, session_id)
    missing  = find_missing(fields, values)
    field_map = {f.key: f for f in fields}

    return [
        {
            "key": m.key,
            "label": m.label,
            "type": m.type,
            "required": field_map[m.key].required,
        }
        for m in missing
        if m.key in field_map
    ]


@router.post("/{session_id}/answers")
def submit_answers(session_id: str, template_id: str, body: UserAnswers, db: DBSession = Depends(get_db)):
    """Saves user-provided answers. Returns any still-missing REQUIRED fields."""
    updates = {a.key: a.value for a in body.answers}
    sessions_repo.save_field_values(db, session_id, updates, source="user")

    fields     = get_fields(template_id)
    all_values = sessions_repo.get_field_values(db, session_id)
    still_missing_required = find_missing_required(fields, all_values)

    return {"still_missing": still_missing_required}


@router.post("/{session_id}/confirm")
def confirm(session_id: str, db: DBSession = Depends(get_db)):
    """Marks the session as confirmed — enables the generate buttons."""
    sessions_repo.update_status(db, session_id, "confirmed")
    return {"status": "confirmed"}

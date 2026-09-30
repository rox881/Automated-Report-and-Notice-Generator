import json
from sqlalchemy.orm import Session as DBSession
from app.db.models import Session, FieldValue


def create_session(db: DBSession, session_id: str, context: str, created_at: str) -> Session:
    session = Session(id=session_id, context=context, status="extracted", created_at=created_at)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: DBSession, session_id: str) -> Session | None:
    return db.query(Session).filter(Session.id == session_id).first()


def update_status(db: DBSession, session_id: str, status: str):
    db.query(Session).filter(Session.id == session_id).update({"status": status})
    db.commit()


def save_field_values(db: DBSession, session_id: str, values: dict, source: str):
    """Upserts field values. Existing LLM values are overwritten when source='user'."""
    for key, value in values.items():
        value_json = json.dumps(value) if isinstance(value, (list, dict)) else str(value) if value is not None else None
        existing = db.query(FieldValue).filter(
            FieldValue.session_id == session_id,
            FieldValue.field_key == key
        ).first()
        if existing:
            existing.value_json = value_json
            existing.source = source
        else:
            db.add(FieldValue(session_id=session_id, field_key=key, value_json=value_json, source=source))
    db.commit()


def get_field_values(db: DBSession, session_id: str) -> dict:
    """Returns {field_key: value} dict. Lists are deserialized from JSON."""
    rows = db.query(FieldValue).filter(FieldValue.session_id == session_id).all()
    result = {}
    for row in rows:
        if row.value_json is None:
            result[row.field_key] = None
        else:
            try:
                result[row.field_key] = json.loads(row.value_json)
            except (json.JSONDecodeError, ValueError):
                result[row.field_key] = row.value_json
    return result


def get_all_sessions(db: DBSession) -> list[Session]:
    return db.query(Session).order_by(Session.created_at.desc()).all()

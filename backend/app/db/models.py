from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"

    id         = Column(String, primary_key=True)
    context    = Column(Text, nullable=False)
    status     = Column(String, nullable=False, default="extracted")  # extracted | needs_input | confirmed
    created_at = Column(String, nullable=False)


class FieldValue(Base):
    __tablename__ = "field_values"

    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    field_key  = Column(String, primary_key=True)
    value_json = Column(Text)           # string or JSON-encoded list
    source     = Column(String, nullable=False)  # 'llm' or 'user'


class Job(Base):
    __tablename__ = "jobs"

    id          = Column(String, primary_key=True)
    session_id  = Column(String, ForeignKey("sessions.id"), nullable=False)
    template_id = Column(String, nullable=False)   # 'notice' or 'report'
    status      = Column(String, nullable=False, default="pending")  # pending | running | done | failed
    output_path = Column(String)
    error       = Column(Text)
    created_at  = Column(String, nullable=False)
    finished_at = Column(String)

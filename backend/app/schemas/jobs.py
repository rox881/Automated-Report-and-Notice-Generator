from pydantic import BaseModel
from typing import Optional


class JobResponse(BaseModel):
    id: str
    session_id: str
    template_id: str
    status: str          # pending | running | done | failed
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    finished_at: Optional[str] = None

    class Config:
        from_attributes = True

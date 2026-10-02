from pydantic import BaseModel
from typing import Literal


class SessionCreate(BaseModel):
    context: str


class SessionResponse(BaseModel):
    id: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


class ReframeRequest(BaseModel):
    section: str
    instruction: str
    current_text: str

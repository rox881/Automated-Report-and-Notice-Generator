from pydantic import BaseModel
from typing import Any, List, Optional


class FieldSpec(BaseModel):
    key: str
    label: str
    type: str            # text | list | number | date
    required: bool
    max_chars: int
    default: Optional[str] = None
    example: Optional[Any] = None


class MissingField(BaseModel):
    key: str
    label: str
    type: str


class FieldAnswer(BaseModel):
    key: str
    value: Any


class UserAnswers(BaseModel):
    answers: List[FieldAnswer]


class FieldPreview(BaseModel):
    key: str
    label: str
    value: Optional[Any]
    source: str          # 'llm' or 'user'

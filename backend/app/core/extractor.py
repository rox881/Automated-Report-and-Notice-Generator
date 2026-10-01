import json
import re
from pathlib import Path
from jinja2 import Template

from app.llm.client import complete
from app.llm.schema_builder import build_field_spec_text
from app.registry.loader import get_fields
from app.utils.errors import ExtractionError

_PROMPTS = Path(__file__).parent.parent / "llm" / "prompts"

# Values that the LLM might output when a field is missing — all treated as None
_EMPTY_STRINGS = {"", "none", "null", "n/a", "tbd", "not specified",
                  "not mentioned", "not found", "unknown", "na"}


def _sanitize(value):
    """
    Converts LLM 'empty-but-not-null' outputs into Python None.
    Handles: empty strings, "N/A", "TBD", "None", "null", empty lists.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in _EMPTY_STRINGS:
        return None
    if isinstance(value, list):
        cleaned = [v for v in value if str(v).strip().lower() not in _EMPTY_STRINGS]
        return cleaned if cleaned else None
    return value


def _extract_json(raw: str) -> dict:
    """
    Robustly extracts a JSON object from the LLM response.
    Handles: pure JSON, JSON with markdown fences, JSON with preamble text.
    Falls back to regex scanning if normal parsing fails.
    """
    raw = raw.strip()

    # Strip markdown fences (```json ... ``` or ``` ... ```)
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: find any JSON object block in the response using regex
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ExtractionError(f"Could not parse JSON from LLM response.\n\nRaw output:\n{raw}")


def extract_fields(template_id: str, context: str) -> dict:
    """
    Calls the LLM to extract field values from raw context text.
    Returns a dict: { field_key: value_or_None }
    Missing/empty LLM values are sanitized to None so the gap_checker can catch them.
    """
    fields = get_fields(template_id)
    fields_spec = build_field_spec_text(fields)

    system_prompt = (_PROMPTS / "extract_system.md").read_text(encoding="utf-8")
    user_template = Template((_PROMPTS / "extract_user.md.j2").read_text(encoding="utf-8"))
    user_prompt = user_template.render(fields_spec=fields_spec, context=context)

    raw = complete(system_prompt, user_prompt)
    data = _extract_json(raw)

    # Support both {"fields": {...}} and flat {"key": "value"} responses
    if "fields" in data and isinstance(data["fields"], dict):
        extracted = data["fields"]
    else:
        # Flat response — filter to only known field keys
        known_keys = {f.key for f in fields}
        extracted = {k: v for k, v in data.items() if k in known_keys}

    # Sanitize all values: convert fake "N/A", "", "None" -> None
    return {key: _sanitize(val) for key, val in extracted.items()}

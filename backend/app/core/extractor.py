import json
from pathlib import Path
from jinja2 import Template

from app.llm.client import complete
from app.llm.schema_builder import build_field_spec_text
from app.registry.loader import get_fields
from app.utils.errors import ExtractionError

_PROMPTS = Path(__file__).parent.parent / "llm" / "prompts"


def extract_fields(template_id: str, context: str) -> dict:
    """
    Calls the LLM to extract field values from raw context text.
    Returns a dict: { field_key: value_or_None }
    Raises ExtractionError if LLM returns invalid JSON.
    """
    fields = get_fields(template_id)
    fields_spec = build_field_spec_text(fields)

    system_prompt = (_PROMPTS / "extract_system.md").read_text(encoding="utf-8")
    user_template = Template((_PROMPTS / "extract_user.md.j2").read_text(encoding="utf-8"))
    user_prompt = user_template.render(fields_spec=fields_spec, context=context)

    raw = complete(system_prompt, user_prompt).strip()

    # Strip markdown code fences if the model wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    try:
        data = json.loads(raw)
        return data.get("fields", {})
    except (json.JSONDecodeError, KeyError) as e:
        raise ExtractionError(f"LLM returned invalid JSON: {e}\n\nRaw output:\n{raw}")

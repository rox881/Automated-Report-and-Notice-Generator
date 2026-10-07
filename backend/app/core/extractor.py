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


def synthesize_report_narrative(context: str, extracted_metadata: dict) -> dict:
    """
    Synthesizes academic Introduction, multi-paragraph Discussion, and Conclusion
    with dynamic bold highlights tailored to the event context.
    """
    prompt_path = _PROMPTS / "report_synthesis.md"
    if not prompt_path.exists():
        return {}

    system_prompt = prompt_path.read_text(encoding="utf-8")
    user_prompt = f"""EVENT METADATA:
{json.dumps(extracted_metadata, indent=2)}

RAW CONTEXT:
{context}

Draft the introduction, discussion, and conclusion in JSON format."""

    try:
        raw = complete(system_prompt, user_prompt)
        data = _extract_json(raw)
        return {
            "introduction": data.get("introduction"),
            "discussion": data.get("discussion"),
            "conclusion": data.get("conclusion"),
        }
    except Exception as e:
        print(f"[ERROR] Narrative synthesis failed: {e}")
        return {}


def reframe_section(
    section_name: str,
    current_text: str,
    instruction: str,
    context: str = "",
    metadata: dict = None,
) -> str:
    """
    Reframes or regenerates an existing report section (Introduction, Discussion, Conclusion)
    using user instruction or preset choice, backed by full event context and metadata.
    """
    prompt_path = _PROMPTS / "reframe_prompt.md"
    system_prompt = (
        prompt_path.read_text(encoding="utf-8")
        if prompt_path.exists()
        else "You are an expert report editor. Rewrite the text."
    )

    metadata_str = json.dumps(metadata or {}, indent=2)

    user_prompt = f"""EVENT METADATA:
{metadata_str}

EVENT CONTEXT:
{context or 'No additional raw context provided.'}

SECTION TO GENERATE/REFRAME: {section_name}

USER INSTRUCTION:
{instruction}

CURRENT SECTION TEXT (may be empty):
{current_text or '(None - draft from scratch)'}

Provide the section in JSON with key 'reframed_text'."""

    try:
        raw = complete(system_prompt, user_prompt)
        data = _extract_json(raw)
        reframed = data.get("reframed_text")
        if not reframed and current_text:
            return current_text
        return reframed or ""
    except Exception as e:
        print(f"[ERROR] reframe_section failed: {e}")
        return current_text or ""


def extract_fields(template_id: str, context: str) -> dict:
    """
    Calls the LLM to extract field values from raw context text.
    For report templates, synthesizes Introduction, Discussion, and Conclusion
    if not already provided in the source text.
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
        known_keys = {f.key for f in fields}
        extracted = {k: v for k, v in data.items() if k in known_keys}

    # Sanitize all extracted values
    result = {key: _sanitize(val) for key, val in extracted.items()}

    # If this is the report template, synthesize narrative fields if empty or too brief
    if template_id == "report":
        def _needs_narrative(k):
            val = result.get(k)
            if val is None:
                return True
            s = str(val).strip()
            # If empty or too brief to be an academic report narrative (e.g., just an event title or short fragment)
            return len(s) < 100

        narratives_needed = any(
            _needs_narrative(k)
            for k in ("introduction", "discussion", "conclusion")
        )
        if narratives_needed:
            narrative = synthesize_report_narrative(context, result)
            for k in ("introduction", "discussion", "conclusion"):
                if _needs_narrative(k) and narrative.get(k):
                    result[k] = narrative[k]

    return result

from datetime import datetime
from app.schemas.fields import FieldSpec


def format_value(spec: FieldSpec, value) -> str | list | None:
    """Applies typed formatting rules to a single field value."""
    if value is None:
        return spec.default or ""

    if spec.type == "date":
        return _format_date(str(value))
    elif spec.type == "list":
        return value if isinstance(value, list) else [str(value)]
    elif spec.type in ("text", "number"):
        return str(value).strip()

    return value


def _format_date(value: str) -> str:
    """Normalizes common date formats to DD/MM/YYYY. Returns as-is if unrecognized."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%dth %B %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value  # Return original string if no format matched


def build_context(fields: list[FieldSpec], values: dict) -> dict:
    """
    Builds the final docxtpl render context from confirmed field values.
    Applies formatting rules per field type.
    Special case: speakers list is also joined as 'speakers_block' for notice template.
    """
    context = {}

    for spec in fields:
        value = values.get(spec.key)
        context[spec.key] = format_value(spec, value)

    # speakers_block: newline-joined string for {{ speakers_block }} tag in notice template
    if "speakers" in context and isinstance(context["speakers"], list):
        context["speakers_block"] = "\n".join(context["speakers"])

    return context

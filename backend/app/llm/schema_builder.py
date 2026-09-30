from app.schemas.fields import FieldSpec


def build_field_spec_text(fields: list[FieldSpec]) -> str:
    """
    Converts a list of FieldSpec objects into a plain-text table
    that is injected into the extraction prompt.

    Output format (one field per line):
        key | label | type | required/optional | max_chars
    """
    lines = ["key | label | type | required | max_chars"]
    lines.append("-" * 60)
    for f in fields:
        req = "required" if f.required else "optional"
        lines.append(f"{f.key} | {f.label} | {f.type} | {req} | {f.max_chars}")
    return "\n".join(lines)

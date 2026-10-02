from app.schemas.fields import FieldSpec, MissingField

# Strings that count as "no value" even if they are not Python None
_EMPTY_STRINGS = {"", "none", "null", "n/a", "tbd", "not specified",
                  "not mentioned", "not found", "unknown", "na"}

# Narrative fields are synthesized by AI and reviewed in Step 3 — never prompted in Step 2 form
_NARRATIVE_FIELDS = {"introduction", "discussion", "conclusion"}


def _is_empty(value) -> bool:
    """Returns True if a value should be treated as missing/not provided."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in _EMPTY_STRINGS:
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def find_missing(fields: list[FieldSpec], values: dict) -> list[MissingField]:
    """
    Returns ONLY required factual fields that have no value.
    Narrative fields (introduction, discussion, conclusion) and optional
    photo captions are excluded so the user is never asked to manually write essays.
    """
    missing = []
    for spec in fields:
        if spec.key in _NARRATIVE_FIELDS:
            continue
        if spec.required and _is_empty(values.get(spec.key)):
            missing.append(
                MissingField(key=spec.key, label=spec.label, type=spec.type)
            )
    return missing


def find_missing_required(fields: list[FieldSpec], values: dict) -> list[str]:
    """
    Returns only the keys of required factual fields with empty values.
    Used to decide if saving answers still leaves required factual fields unfilled.
    """
    return [
        spec.key
        for spec in fields
        if spec.key not in _NARRATIVE_FIELDS
        and spec.required
        and _is_empty(values.get(spec.key))
    ]

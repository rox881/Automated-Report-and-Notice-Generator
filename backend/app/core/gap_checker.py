from app.schemas.fields import FieldSpec, MissingField

# Strings that count as "no value" even if they are not Python None
_EMPTY_STRINGS = {"", "none", "null", "n/a", "tbd", "not specified",
                  "not mentioned", "not found", "unknown", "na"}


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
    Returns ONLY required fields that have no value.
    Optional fields (e.g. photo captions with defaults) are excluded —
    they appear in the preview table but never in the missing-fields form.
    """
    missing = []
    for spec in fields:
        if spec.required and _is_empty(values.get(spec.key)):
            missing.append(
                MissingField(key=spec.key, label=spec.label, type=spec.type)
            )
    return missing


def find_missing_required(fields: list[FieldSpec], values: dict) -> list[str]:
    """
    Returns only the keys of required fields with empty values.
    Used to decide if saving answers still leaves required fields unfilled.
    """
    return [
        spec.key
        for spec in fields
        if spec.required and _is_empty(values.get(spec.key))
    ]

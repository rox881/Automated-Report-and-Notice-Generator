from app.schemas.fields import FieldSpec


def validate_fields(fields: list[FieldSpec], values: dict) -> list[str]:
    """
    Validates extracted/confirmed field values against the spec.
    Returns a list of error messages. Empty list = all valid.
    """
    errors = []

    for spec in fields:
        value = values.get(spec.key)

        # Required check
        if value is None:
            if spec.required:
                errors.append(f"'{spec.key}' is required but missing.")
            continue

        # Type checks
        if spec.type == "text" and not isinstance(value, str):
            errors.append(f"'{spec.key}' must be a string, got {type(value).__name__}.")

        elif spec.type == "list":
            if not isinstance(value, list):
                errors.append(f"'{spec.key}' must be a list, got {type(value).__name__}.")

        elif spec.type == "number":
            try:
                int(str(value).strip())
            except ValueError:
                errors.append(f"'{spec.key}' must be a number, got '{value}'.")

        # max_chars check (text and number only)
        if isinstance(value, str) and len(value) > spec.max_chars:
            errors.append(
                f"'{spec.key}' exceeds max_chars limit ({len(value)} > {spec.max_chars})."
            )

    return errors

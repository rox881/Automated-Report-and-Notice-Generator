from app.schemas.fields import FieldSpec, MissingField


def find_missing(fields: list[FieldSpec], values: dict) -> list[MissingField]:
    """
    Returns a list of required fields that have no value (None or absent).
    These are the fields the UI must ask the user to fill in.
    """
    missing = []
    for spec in fields:
        if spec.required and values.get(spec.key) is None:
            missing.append(MissingField(key=spec.key, label=spec.label, type=spec.type))
    return missing

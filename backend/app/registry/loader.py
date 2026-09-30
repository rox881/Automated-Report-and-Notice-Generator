import json
from pathlib import Path
from app.schemas.fields import FieldSpec
from app.config import settings

_registry: dict[str, list[FieldSpec]] = {}


def load_all() -> dict[str, list[FieldSpec]]:
    """
    Reads every templates/{name}/fields.json on startup.
    Populates the in-memory registry.
    """
    global _registry
    templates_dir = Path(settings.templates_dir)

    for template_dir in templates_dir.iterdir():
        if not template_dir.is_dir():
            continue
        fields_file = template_dir / "fields.json"
        if not fields_file.exists():
            continue
        with open(fields_file, encoding="utf-8") as f:
            data = json.load(f)
        template_id = data["template_id"]
        _registry[template_id] = [FieldSpec(**field) for field in data["fields"]]

    return _registry


def get_fields(template_id: str) -> list[FieldSpec]:
    """Returns the field spec list for a given template_id."""
    if not _registry:
        load_all()
    return _registry.get(template_id, [])


def get_all_template_ids() -> list[str]:
    if not _registry:
        load_all()
    return list(_registry.keys())

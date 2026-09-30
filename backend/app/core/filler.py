from pathlib import Path
from docxtpl import DocxTemplate

from app.config import settings
from app.utils.errors import FillerError


def fill_template(template_id: str, context: dict, output_path: str) -> str:
    """
    Fills a copy of the template.docx with the given context values.
    Saves the rendered document to output_path.
    Returns output_path on success.
    Raises FillerError on failure.
    """
    template_file = Path(settings.templates_dir) / template_id / "template.docx"

    if not template_file.exists():
        raise FillerError(f"Template file not found: {template_file}")

    try:
        tpl = DocxTemplate(str(template_file))
        tpl.render(context)
        tpl.save(output_path)
        return output_path
    except Exception as e:
        raise FillerError(f"docxtpl render failed for '{template_id}': {e}")

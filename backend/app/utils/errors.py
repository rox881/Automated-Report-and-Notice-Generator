class ExtractionError(Exception):
    """LLM extraction failed or returned invalid output."""
    pass


class ValidationError(Exception):
    """Field value failed type or constraint validation."""
    pass


class FillerError(Exception):
    """docxtpl template rendering failed."""
    pass


class RegistryError(Exception):
    """Template registry loading failed (missing fields.json or template.docx)."""
    pass

import re
from datetime import datetime
from docxtpl import RichText

from app.schemas.fields import FieldSpec

_NARRATIVE_FIELDS = {"introduction", "discussion", "conclusion"}


def text_to_richtext(text: str) -> RichText:
    """
    Parses a string containing markdown bold/italic (**bold**, *italic*)
    or HTML tags (<b>bold</b>, <i>italic</i>, <br>, <p>) into a docxtpl.RichText object.
    Preserves bold highlights and paragraph breaks in the Word output.
    """
    if not text:
        return RichText("")

    s = str(text)
    # Normalize HTML tags to markdown / newlines
    s = re.sub(r"<\s*br\s*/?\s*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</\s*p\s*>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*p\s*>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"</\s*div\s*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*div\s*>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*strong\s*>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"</\s*strong\s*>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*b\s*>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"</\s*b\s*>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*em\s*>", "*", s, flags=re.IGNORECASE)
    s = re.sub(r"</\s*em\s*>", "*", s, flags=re.IGNORECASE)
    s = re.sub(r"<\s*i\s*>", "*", s, flags=re.IGNORECASE)
    s = re.sub(r"</\s*i\s*>", "*", s, flags=re.IGNORECASE)

    # Tokenize by markdown bold (**...**) and italic (*...*)
    token_pattern = re.compile(r"(\*\*.*?\*\*|\*[^*\n]+?\*)")
    tokens = token_pattern.split(s)

    rt = RichText()
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) >= 4:
            rt.add(token[2:-2], bold=True)
        elif token.startswith("*") and token.endswith("*") and len(token) >= 2:
            rt.add(token[1:-1], italic=True)
        else:
            rt.add(token)

    return rt


def format_value(spec: FieldSpec, value):
    """Applies typed formatting rules to a single field value."""
    if value is None:
        return spec.default or ""

    if spec.key in _NARRATIVE_FIELDS:
        return text_to_richtext(value)

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
    return value


def build_context(fields: list[FieldSpec], values: dict) -> dict:
    """
    Builds the final docxtpl render context from confirmed field values.
    Narrative fields (introduction, discussion, conclusion) are converted to RichText
    objects to guarantee real bolding and paragraph breaks in Microsoft Word.
    """
    context = {}

    for spec in fields:
        value = values.get(spec.key)
        context[spec.key] = format_value(spec, value)

    # speakers_block: newline-joined string for {{ speakers_block }} tag in notice template
    if "speakers" in context and isinstance(context["speakers"], list):
        context["speakers_block"] = "\n".join(context["speakers"])

    return context

from pathlib import Path
from datetime import datetime, timezone
from app.config import settings


def get_output_path(session_id: str, template_id: str) -> str:
    """
    Returns a unique, versioned output file path.
    Format: output/{template_id}_{session_id[:8]}_{YYYYMMDD_HHMMSS}.docx
    Creates the output directory if it does not exist.
    """
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename  = f"{template_id}_{session_id[:8]}_{timestamp}.docx"
    return str(output_dir / filename)

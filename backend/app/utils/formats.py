def title_case(value: str) -> str:
    """Converts a string to title case."""
    return value.title() if value else value


def format_speakers_list(speakers: list) -> str:
    """Joins a list of speakers into a newline-separated string."""
    return "\n".join(speakers) if speakers else ""


def truncate(value: str, max_chars: int) -> str:
    """Truncates a string to max_chars, appending '...' if cut."""
    if value and len(value) > max_chars:
        return value[:max_chars].rstrip() + "..."
    return value

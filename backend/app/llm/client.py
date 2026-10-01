import requests
from app.config import settings
from app.utils.errors import ExtractionError


def complete(system: str, user: str) -> str:
    """
    Calls the Groq API (OpenAI-compatible) with JSON mode enforced.
    JSON mode guarantees the model returns valid JSON with zero preamble or markdown fences.
    """
    if not settings.llm_api_key or settings.llm_api_key.startswith("your_"):
        raise ExtractionError(
            "Groq API key is missing. Set LLM_API_KEY (starts with 'gsk_') in your .env file."
        )

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},  # Enforce native JSON mode on Groq
    }

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            raise ExtractionError(
                f"Groq API returned status {response.status_code}: {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.RequestException as e:
        raise ExtractionError(f"Network error connecting to Groq API: {e}")

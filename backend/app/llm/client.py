import requests
from app.config import settings
from app.utils.errors import ExtractionError


def complete(system: str, user: str) -> str:
    """
    Calls the xAI Grok API via its OpenAI-compatible endpoint.
    Default endpoint: https://api.x.ai/v1/chat/completions
    """
    if not settings.llm_api_key or settings.llm_api_key.startswith("your_"):
        raise ExtractionError(
            "Grok API key is missing. Please set LLM_API_KEY in your .env file with your xAI key."
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
        "temperature": 0.1,  # Low temperature for strict factual extraction
    }

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            raise ExtractionError(
                f"Grok API returned status {response.status_code}: {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.RequestException as e:
        raise ExtractionError(f"Network error while connecting to Grok API: {e}")

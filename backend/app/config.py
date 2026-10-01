from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings

# Absolute path to the project root (Report Generator/)
# This file is at: backend/app/config.py → parent.parent.parent = project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"

    # These defaults are absolute. If .env overrides them with relative paths,
    # the model_validator below converts them to absolute using ROOT_DIR.
    db_path: str = str(ROOT_DIR / "app.db")
    output_dir: str = str(ROOT_DIR / "output")
    templates_dir: str = str(ROOT_DIR / "templates")

    @model_validator(mode="after")
    def resolve_relative_paths(self):
        """
        If any path from .env is relative (e.g. ./templates),
        resolve it to an absolute path anchored at the project ROOT_DIR.
        This means the app works correctly regardless of which directory
        uvicorn is launched from.
        """
        for field_name in ("db_path", "output_dir", "templates_dir"):
            val = getattr(self, field_name)
            p = Path(val)
            if not p.is_absolute():
                setattr(self, field_name, str((ROOT_DIR / p).resolve()))
        return self

    class Config:
        env_file = str(ROOT_DIR / ".env")
        extra = "ignore"


settings = Settings()

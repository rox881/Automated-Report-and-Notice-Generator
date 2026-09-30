from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_model: str = "grok-2-latest"
    llm_base_url: str = "https://api.x.ai/v1"
    db_path: str = "./app.db"
    output_dir: str = "./output"
    templates_dir: str = "./templates"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

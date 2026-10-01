from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    db_path: str = "./app.db"
    output_dir: str = "./output"
    templates_dir: str = "./templates"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "capstone-ml-service"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "kada"

    model_path: str = "saved_models/model.joblib"
    metadata_path: str = "saved_models/metadata.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate
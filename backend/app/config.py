from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/verkeersboete"

    # Anthropic
    anthropic_api_key: str = ""

    # Application
    secret_key: str = "change-me-in-production"
    upload_dir: str = "./uploads"
    generated_dir: str = "./generated"

    # OCR
    ocr_engine: str = "tesseract"  # "tesseract" or "google_vision"
    google_application_credentials: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def ensure_dirs(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.generated_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()

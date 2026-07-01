from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "postgresql://postgres:postgres@db:5432/cvcoach"
    app_name: str = "CV Coach"
    app_env: str = "development"
    debug: bool = True
    tessdata_prefix: str = "/usr/share/tesseract-ocr/4.00/tessdata"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

settings = Settings()

if not settings.openai_api_key:
    print("WARNING: OPENAI_API_KEY not set")

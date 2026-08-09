import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Edufeedia API")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./edufeedia.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "edufeedia-super-secret-secure-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

settings = Settings()

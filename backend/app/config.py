import os
from pathlib import Path
from dotenv import load_dotenv

# Absolute path to the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Edufeedia API")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "edufeedia-super-secret-secure-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "*")

    def __init__(self):
        # Strict security validation for production deployments
        if self.ENVIRONMENT == "production":
            if not os.getenv("SECRET_KEY") or "change-in-production" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("CRITICAL SECURITY ERROR: Production environment requires an explicitly set, random 32+ char SECRET_KEY.")
            if self.ALLOWED_ORIGINS_RAW == "*":
                raise ValueError("CRITICAL SECURITY ERROR: Production environment cannot use wildcard '*' ALLOWED_ORIGINS.")
            
            # Database check: Production must run PostgreSQL
            db_url = os.getenv("DATABASE_URL", "")
            if not db_url or "sqlite" in db_url.lower():
                raise ValueError("CRITICAL CONFIG ERROR: Production environment must use RDS/PostgreSQL database (sqlite not permitted).")

            # Cache check: Production requires Redis
            redis_url = os.getenv("REDIS_URL", "")
            if not redis_url:
                raise ValueError("CRITICAL CONFIG ERROR: Production environment requires REDIS_URL for OTP and token cache.")

            # Email check: Production requires live SMTP provider for verifiable parental consent
            smtp_host = os.getenv("SMTP_HOST", "")
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_pass = os.getenv("SMTP_PASSWORD", "")
            if not (smtp_host and smtp_user and smtp_pass):
                raise ValueError("CRITICAL CONFIG ERROR: Production environment requires valid SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) for legal guardian consent dispatch.")

    @property
    def ALLOWED_ORIGINS(self) -> list:
        if self.ENVIRONMENT == "production" and self.ALLOWED_ORIGINS_RAW == "*":
            return ["https://edufeedia.com"]
        if self.ALLOWED_ORIGINS_RAW == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

    @property
    def DATABASE_URL(self) -> str:
        raw_url = os.getenv("DATABASE_URL", "")
        if not raw_url or raw_url.startswith("sqlite:///."):
            db_file = (BASE_DIR / "edufeedia.db").resolve().as_posix()
            return f"sqlite:///{db_file}"
        return raw_url

settings = Settings()

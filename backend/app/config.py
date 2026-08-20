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
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Explicit development vs production origins
    DEFAULT_DEV_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", DEFAULT_DEV_ORIGINS)

    # Restricted CORS methods and headers
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["Authorization", "Content-Type", "X-Requested-With", "X-Request-ID", "Accept", "Origin"]

    def __init__(self):
        # Resolve SECRET_KEY safely without hardcoded production fallbacks
        env_secret = os.getenv("SECRET_KEY")
        if self.ENVIRONMENT == "production":
            if not env_secret or len(env_secret) < 32 or "change-in-production" in env_secret:
                raise ValueError("CRITICAL CONFIG ERROR: Production environment requires a strong, random 32+ char SECRET_KEY set via environment variable.")
            self.SECRET_KEY = env_secret
            
            if self.ALLOWED_ORIGINS_RAW == "*":
                raise ValueError("CRITICAL CONFIG ERROR: Production environment cannot use wildcard '*' ALLOWED_ORIGINS.")
            
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
        else:
            # Development/Testing environment fallback
            self.SECRET_KEY = env_secret or "edufeedia-dev-only-insecure-test-signing-key-32chars"

    @property
    def ALLOWED_ORIGINS(self) -> list:
        if self.ENVIRONMENT == "production" and self.ALLOWED_ORIGINS_RAW == "*":
            return ["https://app.edufeedia.com", "https://edufeedia.com"]
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

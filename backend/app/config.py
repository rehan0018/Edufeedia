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
        env_secret = os.getenv("SECRET_KEY")
        if self.ENVIRONMENT == "production":
            forbidden_patterns = ["change-in-production", "edufeedia_dev", "dev-only", "secret_key_2026", "insecure-test"]
            if not env_secret or len(env_secret) < 32 or any(p in env_secret.lower() for p in forbidden_patterns):
                errors.append("• SECRET_KEY: Must be a strong, random 32+ character string (cannot use default development placeholders).")
            
            if self.ALLOWED_ORIGINS_RAW == "*":
                errors.append("• ALLOWED_ORIGINS: Wildcard '*' is disallowed in production. Provide comma-separated origins (e.g. 'https://app.edufeedia.com').")
            
            db_url = os.getenv("DATABASE_URL", "")
            if not db_url or "sqlite" in db_url.lower():
                errors.append("• DATABASE_URL: Production requires a managed PostgreSQL database (e.g. Render PostgreSQL or Supabase).")

            redis_url = os.getenv("REDIS_URL", "")
            if not redis_url:
                errors.append("• REDIS_URL: Production requires a Redis instance for token blacklisting and OTP verification.")

            smtp_host = os.getenv("SMTP_HOST", "")
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_pass = os.getenv("SMTP_PASSWORD", "")
            if not (smtp_host and smtp_user and smtp_pass):
                errors.append("• SMTP_HOST, SMTP_USER, SMTP_PASSWORD: Required for verifiable parental consent dispatch.")

            if errors:
                err_msg = (
                    "\n======================================================================\n"
                    "CRITICAL CONFIG ERROR: Missing Production Environment Variables\n"
                    "======================================================================\n"
                    + "\n".join(errors) +
                    "\n\n👉 ACTION REQUIRED: Add the variables above in your Render / Cloud Dashboard.\n"
                    "👉 PREVIEW / DEMO MODE: If deploying a lightweight preview/demo without external PostgreSQL/Redis,\n"
                    "   set ENVIRONMENT=staging in your Environment Variables.\n"
                    "======================================================================"
                )
                raise ValueError(err_msg)

            self.SECRET_KEY = env_secret
        else:
            # Development/Staging/Testing fallback
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
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)
        return raw_url

settings = Settings()

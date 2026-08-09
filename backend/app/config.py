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
    SECRET_KEY: str = os.getenv("SECRET_KEY", "edufeedia-super-secret-secure-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    @property
    def DATABASE_URL(self) -> str:
        raw_url = os.getenv("DATABASE_URL", "")
        if not raw_url or raw_url.startswith("sqlite:///."):
            db_file = (BASE_DIR / "edufeedia.db").resolve().as_posix()
            return f"sqlite:///{db_file}"
        return raw_url

settings = Settings()

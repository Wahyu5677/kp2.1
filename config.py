import os
from datetime import timedelta
from pathlib import Path


def _load_dotenv_if_exists():
    """
    Load key=value pairs from .env into os.environ (non-destructive).
    Existing OS environment variables are not overwritten.
    """
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv_if_exists()


def _get_env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://srqtaildhnwmtxwuxfoe.supabase.co")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-fallback-change-me")

    # Session cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _get_env_bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=60 * 15)
    ACCESS_TOKEN_LIFETIME_SECONDS = 60 * 15
    REFRESH_TOKEN_MAX_AGE = 60 * 60 * 24 * 30

    @classmethod
    def validate(cls):
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY belum di-set. "
                "Set environment variable terlebih dahulu (atau isi file .env)."
            )

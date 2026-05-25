from pathlib import Path

from dotenv import load_dotenv

_loaded = False


def load_project_env() -> None:
    """Load .env from project root (and optional app/.env overrides)."""
    global _loaded
    if _loaded:
        return

    app_dir = Path(__file__).resolve().parent
    project_root = app_dir.parent
    load_dotenv(project_root / ".env")
    load_dotenv(app_dir / ".env", override=True)
    _loaded = True

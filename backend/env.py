from pathlib import Path

from dotenv import load_dotenv

_loaded = False


def load_project_env() -> None:
    """Load .env from the backend directory."""
    global _loaded
    if _loaded:
        return

    backend_dir = Path(__file__).resolve().parent
    load_dotenv(backend_dir / ".env")
    _loaded = True

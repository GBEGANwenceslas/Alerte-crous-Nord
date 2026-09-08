"""Configuration du bot, chargée depuis les variables d'environnement (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN", required=True)
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID", required=True)

DEFAULT_BOUNDS = "1.30_51.20_4.30_49.90"
BOUNDS = _get("CROUS_BOUNDS", DEFAULT_BOUNDS)

POLL_INTERVAL_SECONDS = int(_get("POLL_INTERVAL_SECONDS", "300"))
DB_PATH = _get("DB_PATH", "logements_vus.json")

_villes_raw = _get("CROUS_VILLES_FILTRE", "")
VILLES_FILTRE = [v.strip().lower() for v in _villes_raw.split(",") if v.strip()]

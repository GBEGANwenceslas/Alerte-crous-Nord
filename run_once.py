"""Point d'entrée pour une exécution unique d'un cycle de surveillance.

Utilisé par le workflow GitHub Actions (ou n'importe quel cron classique) :
contrairement à `crous_bot/main.py`, ce script ne boucle pas indéfiniment,
il fait une vérification puis s'arrête - c'est le planificateur externe
(cron, GitHub Actions...) qui se charge de le relancer périodiquement.
"""
import logging

from crous_bot import config
from crous_bot.crous_client import CrousClient
from crous_bot.main import run_once
from crous_bot.storage import SeenStore
from crous_bot.telegram_notifier import TelegramNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    client = CrousClient()
    store = SeenStore(config.DB_PATH)
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    nb = run_once(client, store, notifier)
    store.save()

    logging.info("%d nouveau(x) logement(s) trouvé(s) sur ce cycle.", nb)

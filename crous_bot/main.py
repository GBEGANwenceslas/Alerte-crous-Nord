"""Logique de surveillance : un cycle = interroger le site CROUS, comparer aux
logements déjà connus, notifier les nouveautés sur Telegram."""
import logging
import time

from crous_bot import config
from crous_bot.crous_client import CrousClient
from crous_bot.storage import SeenStore
from crous_bot.telegram_notifier import TelegramNotifier


def matches_filter(listing_text: str) -> bool:
    if not config.VILLES_FILTRE:
        return True
    text = listing_text.lower()
    return any(ville in text for ville in config.VILLES_FILTRE)


def run_once(
    client: CrousClient,
    store: SeenStore,
    notifier: TelegramNotifier,
    silent_first_run: bool = True,
) -> int:
    tool_id = client.get_active_tool_id()
    logging.info("Phase de recherche active : tool_id=%s", tool_id)

    is_first_run = store.is_empty()
    nb_nouveaux = 0

    for listing in client.iter_listings(tool_id, config.BOUNDS):
        if not matches_filter(listing.details):
            continue
        if store.is_new(listing.key):
            store.mark_seen(listing.key)
            nb_nouveaux += 1
            if not (is_first_run and silent_first_run):
                message = (
                    "🏠 <b>Nouveau logement CROUS disponible !</b>\n\n"
                    f"{listing.title}\n\n"
                    f"{listing.details[:500]}\n\n"
                    f"🔗 {listing.url}"
                )
                notifier.send(message)
                logging.info("Notification envoyée pour %s", listing.url)

    if is_first_run and silent_first_run and nb_nouveaux:
        notifier.send(
            "✅ Surveillance CROUS Nord-Pas-de-Calais initialisée : "
            f"{nb_nouveaux} logement(s) déjà en ligne enregistré(s) "
            "(pas de notification rétroactive). Vous serez alerté(e) pour les prochains."
        )

    return nb_nouveaux


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    client = CrousClient()
    store = SeenStore(config.DB_PATH)
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    logging.info(
        "Démarrage de la surveillance CROUS (zone Nord-Pas-de-Calais). Intervalle : %ss",
        config.POLL_INTERVAL_SECONDS,
    )

    while True:
        try:
            nb = run_once(client, store, notifier)
            store.save()
            logging.info("%d nouveau(x) logement(s) trouvé(s) sur ce cycle.", nb)
        except Exception:
            logging.exception("Erreur durant le cycle de surveillance")
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

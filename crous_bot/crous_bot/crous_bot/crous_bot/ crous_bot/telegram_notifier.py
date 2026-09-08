"""Envoi de notifications via l'API Bot Telegram."""
import logging

import requests

TELEGRAM_API = "https://api.telegram.org"


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, text: str) -> None:
        url = f"{TELEGRAM_API}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logging.error("Échec de l'envoi Telegram : %s", exc)

"""Client pour interroger trouverunlogement.lescrous.fr (site officiel des CROUS)."""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://trouverunlogement.lescrous.fr"
TOOLS_API = f"{BASE_URL}/api/fr/tools"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
        "CrousLogementWatcher-usage-personnel"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}

ACCOMMODATION_LINK_RE = re.compile(r"/tools/(\d+)/accommodations/(\d+)")


@dataclass
class Listing:
    accommodation_id: str
    tool_id: str
    url: str
    title: str
    details: str

    @property
    def key(self) -> str:
        return f"{self.tool_id}:{self.accommodation_id}"


class CrousClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 20):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout

    def get_active_tool_id(self) -> str:
        resp = self.session.get(TOOLS_API, timeout=self.timeout)
        resp.raise_for_status()
        tools = resp.json()
        now = datetime.now(timezone.utc)

        candidates = []
        for tool in tools:
            if not tool.get("enabled") or not tool.get("published"):
                continue
            start = _parse_dt(tool.get("startDate"))
            end = _parse_dt(tool.get("endDate"))
            if start and end and start <= now <= end:
                candidates.append(tool)

        if not candidates:
            candidates = [t for t in tools if t.get("enabled")]
        if not candidates:
            raise RuntimeError("Aucune phase de recherche active trouvée sur l'API CROUS.")

        candidates.sort(key=lambda t: t["id"], reverse=True)
        return str(candidates[0]["id"])

    def iter_listings(self, tool_id: str, bounds: str, max_pages: int = 15) -> Iterator[Listing]:
        page = 1
        while page <= max_pages:
            url = f"{BASE_URL}/tools/{tool_id}/search"
            params = {"bounds": bounds, "page": page}
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                logging.warning("CROUS a répondu %s pour la page %s", resp.status_code, page)
                break

            listings = list(_extract_listings(resp.text, tool_id))
            if not listings:
                break

            yield from listings

            if not _has_next_page(resp.text, page):
                break
            page += 1
            time.sleep(1)


def _parse_dt(value: Optional[str]):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _extract_listings(html: str, tool_id: str) -> Iterator[Listing]:
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=ACCOMMODATION_LINK_RE)
    seen_in_page = set()
    for link in links:
        match = ACCOMMODATION_LINK_RE.search(link.get("href", ""))
        if not match:
            continue
        found_tool_id, accommodation_id = match.groups()
        if accommodation_id in seen_in_page:
            continue
        seen_in_page.add(accommodation_id)

        container = link.find_parent(["article", "li"]) or link.find_parent("div") or link
        text = " ".join(container.stripped_strings)
        title = link.get_text(strip=True) or text[:80] or f"Logement #{accommodation_id}"

        yield Listing(
            accommodation_id=accommodation_id,
            tool_id=found_tool_id,
            url=urljoin(BASE_URL, link["href"]),
            title=title,
            details=text,
        )


def _has_next_page(html: str, current_page: int) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    match = re.search(r"page\s+(\d+)\s+sur\s+(\d+)", text, re.IGNORECASE)
    if match:
        current, total = int(match.group(1)), int(match.group(2))
        return current < total
    next_link = soup.find("a", string=re.compile("suivante", re.IGNORECASE))
    return next_link is not None and not next_link.get("aria-disabled")

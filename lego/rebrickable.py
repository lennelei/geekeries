"""Accès minimal à l'API Rebrickable (v3).

Clé API lue dans ~/.config/rebrickable/api_key (hors du repo, jamais versionnée).
"""

import json
import os
import sys
import urllib.request

KEY_FILE = os.path.expanduser("~/.config/rebrickable/api_key")
BASE_URL = "https://rebrickable.com/api/v3/lego"


def read_key() -> str:
    try:
        with open(KEY_FILE) as f:
            key = f.read().strip()
    except FileNotFoundError:
        sys.exit(f"Clé API Rebrickable introuvable : {KEY_FILE}")
    if not key:
        sys.exit(f"Clé API Rebrickable vide : {KEY_FILE}")
    return key


def get(path: str, key: str | None = None) -> dict:
    """GET sur un chemin relatif à BASE_URL (ou une URL complète)."""
    url = path if path.startswith("http") else f"{BASE_URL}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"key {key or read_key()}",
        "User-Agent": "geekeries-lego/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def get_all(path: str) -> list[dict]:
    """Suit la pagination et renvoie tous les résultats."""
    key = read_key()
    sep = "&" if "?" in path else "?"
    data = get(f"{path}{sep}page_size=1000", key)
    results = data["results"]
    while data.get("next"):
        data = get(data["next"], key)
        results.extend(data["results"])
    return results

"""Accès minimal à l'API Rebrickable (v3).

Clé API lue dans ~/.config/rebrickable/api_key (hors du repo, jamais versionnée).
"""

import csv
import json
import os
import re
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


# ── Inventaire d'un set, ramené aux ID BrickLink ──────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
API_CACHE_DIR = os.path.join(HERE, "cache", "api")
COLORS_FILE = os.path.join(HERE, "colors.csv")


def normalize_set_num(set_num: str) -> str:
    """« 71395 » → « 71395-1 » (format Rebrickable)."""
    return set_num if "-" in set_num else f"{set_num}-1"


def load_set(set_num: str, refresh: bool = False) -> dict:
    """{"set": infos du set, "parts": lignes d'inventaire}, depuis le cache ou l'API."""
    path = os.path.join(API_CACHE_DIR, f"{set_num}.json")
    if os.path.exists(path) and not refresh:
        with open(path) as f:
            return json.load(f)
    print(f"Interrogation de Rebrickable pour {set_num}…", file=sys.stderr)
    data = {
        "set": get(f"sets/{set_num}/"),
        "parts": get_all(f"sets/{set_num}/parts/"),
    }
    os.makedirs(API_CACHE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)
    return data


def _rb_to_bl_colors() -> dict[str, str]:
    """ID couleur Rebrickable → ID BrickLink, via colors.csv (repli)."""
    mapping: dict[str, str] = {}
    if os.path.exists(COLORS_FILE):
        with open(COLORS_FILE, newline="") as f:
            for row in csv.DictReader(f):
                mapping.setdefault(row["rebrickable_id"], row["bl_id"])
    return mapping


def bl_candidates(item: dict) -> list[str]:
    """Réf. BrickLink à essayer pour une pièce, dans l'ordre, sans doublon.

    Rebrickable écrit parfois le suffixe d'impression avec des zéros de tête que
    BrickLink n'a pas (14769pb0469 chez l'un, 14769pb469 chez l'autre) : variante ajoutée.
    """
    ids = [item["id"], *item.get("bl_ids", [])]
    ids += [re.sub(r"(p[br])0+(\d)", r"\1\2", pid) for pid in ids]
    return list(dict.fromkeys(ids))


def set_items(set_data: dict) -> list[dict]:
    """Regroupe l'inventaire par (pièce, couleur) BrickLink, pièces de rechange exclues.

    Chaque élément : id et color (BrickLink), qty, name, elements (n° LEGO),
    bl_ids (toutes les réf. BrickLink connues de la pièce), img_url (photo Rebrickable).
    """
    rb_to_bl = _rb_to_bl_colors()

    def bl_color(color: dict) -> str:
        bl = (color.get("external_ids") or {}).get("BrickLink")
        if bl and bl.get("ext_ids"):
            return str(bl["ext_ids"][0])
        return rb_to_bl.get(str(color["id"]), f"rb{color['id']}")

    items: dict[tuple[str, str], dict] = {}
    for line in set_data["parts"]:
        if line["is_spare"]:
            continue
        part = line["part"]
        bl_ids = part["external_ids"].get("BrickLink") or []
        part_id = part["part_num"] if part["part_num"] in bl_ids or not bl_ids else bl_ids[0]
        key = (part_id, bl_color(line["color"]))
        it = items.setdefault(key, {
            "id": key[0], "color": key[1], "qty": 0, "name": part["name"],
            "elements": [], "bl_ids": bl_ids, "img_url": part["part_img_url"],
        })
        it["qty"] += line["quantity"]
        if line.get("element_id") and line["element_id"] not in it["elements"]:
            it["elements"].append(line["element_id"])
    return list(items.values())

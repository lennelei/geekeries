#!/usr/bin/env python3
"""Génère colors.csv : correspondance couleurs BrickLink → couleurs LEGO officielles.

Source : API Rebrickable (/api/v3/lego/colors/), qui relie pour chaque couleur ses
identifiants BrickLink et LEGO et donne un hex RGB de référence.

Clé API lue dans ~/.config/rebrickable/api_key (hors du repo, jamais versionnée).
À relancer seulement quand de nouvelles couleurs apparaissent ; colors.csv est versionné.
"""

import csv
import json
import os
import re
import sys
import urllib.request

KEY_FILE = os.path.expanduser("~/.config/rebrickable/api_key")
API_URL = "https://rebrickable.com/api/v3/lego/colors/?page_size=1000"
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "colors.csv")


def read_key() -> str:
    try:
        with open(KEY_FILE) as f:
            key = f.read().strip()
    except FileNotFoundError:
        sys.exit(f"Clé API introuvable : {KEY_FILE}")
    if not key:
        sys.exit(f"Clé API vide : {KEY_FILE}")
    return key


def fetch_all(key: str) -> list[dict]:
    results, url = [], API_URL
    while url:
        req = urllib.request.Request(url, headers={
            "Authorization": f"key {key}",
            "User-Agent": "geekeries-lego/1.0",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        results.extend(data["results"])
        url = data.get("next")
    return results


# Abréviations des libellés internes LEGO (« Tr. Lg Blue » → « Transparent Light Blue »)
ABBREV = [
    (r"\bTr\.\s*", "Transparent "),
    (r"\bBr\.\s*", "Bright "),
    (r"\bMedi?\.\s*", "Medium "),
    (r"\b(Lig\.|Lg)\s*", "Light "),
    (r"\bFlu?\.\s*", "Fluorescent "),
    (r"\bRed\.\s*", "Reddish "),
]


def lego_name(descrs: list[str]) -> str:
    # Premier libellé = nom officiel en minuscules (« Medium stone grey »)
    if not descrs:
        return ""
    name = descrs[0].strip().title()
    for pattern, repl in ABBREV:
        name = re.sub(pattern, repl, name)
    return name.strip()


def main() -> None:
    colors = fetch_all(read_key())
    rows: dict[int, dict] = {}
    for c in colors:
        ext = c.get("external_ids") or {}
        bl, lego = ext.get("BrickLink"), ext.get("LEGO")
        if not bl:
            continue
        lego_id = lego["ext_ids"][0] if lego and lego["ext_ids"] else ""
        lego_nm = lego_name(lego["ext_descrs"][0]) if lego and lego["ext_descrs"] else ""
        for bl_id, bl_descrs in zip(bl["ext_ids"], bl["ext_descrs"]):
            if bl_id in rows:  # un même ID BrickLink rattaché à plusieurs couleurs : garder la 1re
                continue
            rows[bl_id] = {
                "bl_id": bl_id,
                "bl_name": bl_descrs[0] if bl_descrs else "",
                "lego_id": lego_id,
                "lego_name": lego_nm,
                "rgb": c["rgb"].upper(),
                "is_trans": int(c["is_trans"]),
                "rebrickable_id": c["id"],
            }

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(next(iter(rows.values())).keys()))
        w.writeheader()
        for bl_id in sorted(rows):
            w.writerow(rows[bl_id])
    print(f"{len(rows)} couleurs BrickLink écrites dans {OUT_FILE}")


if __name__ == "__main__":
    main()

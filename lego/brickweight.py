#!/usr/bin/env python3
"""
Calcule le poids total des pièces d'un set LEGO à partir d'une liste BrickLink (XML)
en croisant avec le catalogue Parts.xml de BrickLink.

Usage:
  python3 brickweight.py <set_inventory.xml> [--catalog Parts.xml] [--output out.csv]
"""

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def load_catalog(catalog_path: Path) -> dict[str, tuple[str, float | None]]:
    """Retourne un dict ITEMID -> (ITEMNAME, ITEMWEIGHT_g)."""
    catalog: dict[str, tuple[str, float | None]] = {}
    tree = ET.parse(catalog_path)
    for item in tree.getroot().findall("ITEM"):
        item_id = (item.findtext("ITEMID") or "").strip()
        name = (item.findtext("ITEMNAME") or "").strip()
        weight_str = (item.findtext("ITEMWEIGHT") or "").strip()
        try:
            weight = float(weight_str) if weight_str else None
        except ValueError:
            weight = None
        if item_id:
            catalog[item_id] = (name, weight)
    return catalog


def load_inventory(inventory_path: Path) -> list[dict]:
    """Retourne la liste des pièces avec ITEMTYPE, ITEMID, COLOR, MINQTY."""
    tree = ET.parse(inventory_path)
    parts = []
    for item in tree.getroot().findall("ITEM"):
        item_type = (item.findtext("ITEMTYPE") or "").strip()
        if item_type != "P":
            continue
        parts.append({
            "ITEMID": (item.findtext("ITEMID") or "").strip(),
            "COLOR":  (item.findtext("COLOR") or "").strip(),
            "MINQTY": int(item.findtext("MINQTY") or 1),
        })
    return parts


def main():
    parser = argparse.ArgumentParser(description="Calcule le poids d'un set LEGO depuis un XML BrickLink.")
    parser.add_argument("inventory", help="Fichier XML de l'inventaire (ex: 71395.xml)")
    parser.add_argument("--catalog", default="Parts.xml", help="Fichier Parts.xml (défaut: Parts.xml)")
    parser.add_argument("--output", default=None, help="Fichier CSV de sortie (défaut: stdout)")
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    catalog_path = Path(args.catalog)

    if not inventory_path.exists():
        sys.exit(f"Fichier introuvable : {inventory_path}")
    if not catalog_path.exists():
        sys.exit(f"Catalogue introuvable : {catalog_path}")

    catalog = load_catalog(catalog_path)
    parts = load_inventory(inventory_path)

    rows = []
    total_weight = 0.0
    missing = []

    for part in parts:
        item_id = part["ITEMID"]
        qty = part["MINQTY"]
        name, unit_weight = catalog.get(item_id, ("?", None))

        if unit_weight is not None:
            line_weight = unit_weight * qty
            total_weight += line_weight
        else:
            line_weight = None
            missing.append(item_id)

        rows.append({
            "ITEMID":       item_id,
            "COLOR":        part["COLOR"],
            "MINQTY":       qty,
            "ITEMNAME":     name,
            "WEIGHT_g":     unit_weight,
            "TOTAL_WEIGHT_g": f"{line_weight:.4f}" if line_weight is not None else "",
        })

    fieldnames = ["ITEMID", "COLOR", "MINQTY", "ITEMNAME", "WEIGHT_g", "TOTAL_WEIGHT_g"]

    if args.output:
        out = open(args.output, "w", newline="", encoding="utf-8")
    else:
        out = sys.stdout

    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    if args.output:
        out.close()

    total_qty = sum(p["MINQTY"] for p in parts)
    distinct = len({p["ITEMID"] for p in parts})

    print(f"\n--- Résumé ---", file=sys.stderr)
    print(f"Références différentes : {distinct}", file=sys.stderr)
    print(f"Total pièces           : {total_qty}", file=sys.stderr)
    print(f"Lignes dans l'XML      : {len(parts)}", file=sys.stderr)
    print(f"Poids total estimé     : {total_weight:.2f} g", file=sys.stderr)
    if missing:
        print(f"Poids inconnu ({len(missing)}) : {', '.join(sorted(set(missing)))}", file=sys.stderr)


if __name__ == "__main__":
    main()

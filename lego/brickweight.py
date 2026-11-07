#!/usr/bin/env python3
"""
Calcule le poids total des pièces d'un set LEGO.

L'inventaire vient de l'API Rebrickable (même cache que generate_inventory.py) ;
les poids viennent du catalogue Parts.xml de BrickLink, Rebrickable n'en fournissant pas.

Usage:
  python3 brickweight.py [71395-1] [--refresh] [--catalog Parts.xml] [--output out.csv]
"""

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import rebrickable


def load_catalog(catalog_path: Path) -> dict[str, tuple[str, float | None]]:
    """Retourne un dict ITEMID -> (ITEMNAME, ITEMWEIGHT_g), alias ALTITEMIDS compris."""
    catalog: dict[str, tuple[str, float | None]] = {}
    aliases: dict[str, tuple[str, float | None]] = {}
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
            for alt in (item.findtext("ALTITEMIDS") or "").split(","):
                if alt.strip():
                    aliases.setdefault(alt.strip(), (name, weight))
    # Un ID principal l'emporte toujours sur un alias
    return {**aliases, **catalog}


def lookup(catalog: dict, part: dict) -> tuple[str, float | None]:
    """Cherche la pièce sous chacune de ses réf. BrickLink candidates."""
    for pid in rebrickable.bl_candidates(part):
        name, weight = catalog.get(pid, (None, None))
        if weight is not None:
            return name, weight
    return catalog.get(part["id"], (None, None))[0] or part["name"], None


def main():
    parser = argparse.ArgumentParser(description="Calcule le poids d'un set LEGO.")
    parser.add_argument("set", nargs="?", default="71395-1",
                        help="numéro de set Rebrickable (défaut : 71395-1)")
    parser.add_argument("--refresh", action="store_true",
                        help="réinterroger l'API au lieu du cache local")
    parser.add_argument("--catalog", default="Parts.xml", help="Fichier Parts.xml (défaut: Parts.xml)")
    parser.add_argument("--output", default=None, help="Fichier CSV de sortie (défaut: stdout)")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        sys.exit(f"Catalogue introuvable : {catalog_path}")

    catalog = load_catalog(catalog_path)
    set_num = rebrickable.normalize_set_num(args.set)
    parts = rebrickable.set_items(rebrickable.load_set(set_num, args.refresh))

    rows = []
    total_weight = 0.0
    missing = []

    for part in parts:
        qty = part["qty"]
        name, unit_weight = lookup(catalog, part)

        if unit_weight is not None:
            line_weight = unit_weight * qty
            total_weight += line_weight
        else:
            line_weight = None
            missing.append(part["id"])

        rows.append({
            "ITEMID":         part["id"],
            "COLOR":          part["color"],
            "ELEMENT_ID":     part["elements"][0] if part["elements"] else "",
            "MINQTY":         qty,
            "ITEMNAME":       name,
            "WEIGHT_g":       unit_weight,
            "TOTAL_WEIGHT_g": f"{line_weight:.4f}" if line_weight is not None else "",
        })

    fieldnames = ["ITEMID", "COLOR", "ELEMENT_ID", "MINQTY", "ITEMNAME", "WEIGHT_g", "TOTAL_WEIGHT_g"]

    if args.output:
        out = open(args.output, "w", newline="", encoding="utf-8")
    else:
        out = sys.stdout

    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    if args.output:
        out.close()

    total_qty = sum(p["qty"] for p in parts)
    distinct = len({p["id"] for p in parts})

    print(f"\n--- Résumé ({set_num}) ---", file=sys.stderr)
    print(f"Références différentes : {distinct}", file=sys.stderr)
    print(f"Total pièces           : {total_qty}", file=sys.stderr)
    print(f"Lignes d'inventaire    : {len(parts)}", file=sys.stderr)
    print(f"Poids total estimé     : {total_weight:.2f} g", file=sys.stderr)
    if missing:
        print(f"Poids inconnu ({len(missing)}) : {', '.join(sorted(set(missing)))}", file=sys.stderr)


if __name__ == "__main__":
    main()

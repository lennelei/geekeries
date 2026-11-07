#!/usr/bin/env python3
"""Génère une liste de souhaits BrickLink (XML) depuis un CSV de pièces manquantes.

Le CSV (ex. 71395_manquants.csv) porte les réf. et couleurs BrickLink, la quantité
voulue et une note libre. Import sur BrickLink : Want → Upload, coller le XML.

Usage : python3 wanted_list.py 71395_manquants.csv [--output 71395_wanted.xml]
"""

import argparse
import csv
import sys
from pathlib import Path
from xml.sax.saxutils import escape


def item_xml(row: dict) -> str:
    remarks = f"\n<REMARKS>{escape(row['note'])}</REMARKS>" if row.get("note") else ""
    return (
        "<ITEM>\n"
        "<ITEMTYPE>P</ITEMTYPE>\n"
        f"<ITEMID>{escape(row['bl_part'])}</ITEMID>\n"
        f"<COLOR>{escape(row['bl_color'])}</COLOR>\n"
        f"<MINQTY>{int(row['qty'])}</MINQTY>\n"
        "<CONDITION>X</CONDITION>\n"
        f"<NOTIFY>N</NOTIFY>{remarks}\n"
        "</ITEM>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", help="CSV des pièces manquantes")
    parser.add_argument("--output", help="fichier XML (défaut : <set>_wanted.xml)")
    args = parser.parse_args()

    src = Path(args.csv)
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"Aucune pièce dans {src}")

    out = Path(args.output) if args.output else src.with_name(
        src.stem.removesuffix("_manquants") + "_wanted.xml")
    xml = "<INVENTORY>\n" + "\n".join(item_xml(r) for r in rows) + "\n</INVENTORY>\n"
    out.write_text(xml, encoding="utf-8")
    print(f"{out} : {len(rows)} références, {sum(int(r['qty']) for r in rows)} pièces")


if __name__ == "__main__":
    main()

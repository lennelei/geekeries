#!/usr/bin/env python3
"""Generate a multi-column printable HTML inventory from a BrickLink XML wanted list."""

import xml.etree.ElementTree as ET
import html as html_mod
import os, sys, time, urllib.request, urllib.error
from datetime import date
from collections import defaultdict

# ── Configuration ──────────────────────────────────────────────────────────────
INVENTORY_FILE = "71395.xml"
PARTS_CATALOG  = "Parts.xml"
OUTPUT_FILE    = "71395_inventory.html"
CACHE_DIR      = "cache/images"
NUM_COLS       = 3   # 3 or 4 columns of pieces per row on A4

# BrickLink color IDs → display names
# Source: https://v2.bricklink.com/en-fr/catalog/color-guide + visual verification
BRICKLINK_COLORS = {
    # Solid
    "1":   "White",
    "2":   "Tan",
    "3":   "Yellow",
    "4":   "Orange",
    "5":   "Red",
    "6":   "Green",
    "7":   "Blue",           # ancien ID BrickLink, vérifié visuellement
    "8":   "Brown",
    "9":   "Light Gray",
    "10":  "Dark Gray",
    "11":  "Black",
    "24":  "Purple",
    "25":  "Salmon",
    "26":  "Light Salmon",
    "27":  "Rust",
    "28":  "Nougat",
    "29":  "Earth Orange",
    "31":  "Medium Orange",
    "32":  "Light Orange",
    "33":  "Light Yellow",
    "34":  "Lime",
    "35":  "Light Lime",
    "36":  "Bright Green",
    "37":  "Medium Green",
    "38":  "Light Green",
    "39":  "Dark Turquoise",
    "40":  "Light Turquoise",
    "41":  "Aqua",
    "42":  "Medium Blue",
    "43":  "Violet",
    "44":  "Light Violet",
    "47":  "Dark Pink",
    "48":  "Sand Green",
    "49":  "Very Light Gray",
    "54":  "Sand Purple",
    "55":  "Sand Blue",
    "58":  "Sand Red",
    "59":  "Dark Red",
    "62":  "Light Blue",
    "63":  "Dark Blue",
    "66":  "Pearl Light Gray",
    "68":  "Dark Orange",
    "69":  "Dark Tan",
    "71":  "Magenta",
    "72":  "Maersk Blue",
    "73":  "Medium Violet",
    "76":  "Medium Lime",
    "80":  "Dark Green",
    "83":  "Pearl White",
    "85":  "Dark Bluish Gray",
    "86":  "Light Bluish Gray",
    "87":  "Sky Blue",
    "88":  "Reddish Brown",
    "89":  "Dark Purple",
    "90":  "Light Nougat",
    "91":  "Light Brown",
    "93":  "Light Purple",
    "94":  "Medium Dark Pink",
    "95":  "Flat Silver",
    "96":  "Very Light Orange",
    "97":  "Royal Blue",
    "99":  "Very Light Bluish Gray",
    "103": "Bright Light Yellow",
    "104": "Bright Pink",
    "105": "Bright Light Blue",
    "109": "Dark Royal Blue",
    "110": "Bright Light Orange",
    "115": "Warm Gold",       # vérifié visuellement (étoile or/jaune)
    "119": "Pearl Very Light Gray",
    "120": "Dark Brown",
    "150": "Medium Nougat",
    "152": "Light Aqua",
    "153": "Dark Azure",
    "154": "Lavender",
    "155": "Olive Green",
    "156": "Medium Azure",
    "157": "Medium Lavender",
    "158": "Yellowish Green",
    "161": "Dark Yellow",
    "165": "Neon Orange",
    "166": "Neon Green",
    "240": "Medium Brown",
    "241": "Medium Tan",
    "242": "Dark Olive Green",
    # Transparent
    "12":  "Trans-Clear",
    "13":  "Trans-Brown",
    "14":  "Trans-Dark Blue",
    "15":  "Trans-Light Blue",
    "16":  "Trans-Neon Green",
    "17":  "Trans-Red",
    "18":  "Trans-Neon Orange",
    "19":  "Trans-Yellow",
    "20":  "Trans-Green",
    # Chrome / Pearl
    "21":  "Chrome Gold",
    "22":  "Chrome Silver",
    "52":  "Chrome Blue",
    "57":  "Chrome Antique Brass",
    "64":  "Chrome Green",
    "82":  "Chrome Pink",
    "95":  "Flat Silver",
    "122": "Chrome Black",
}

# ── Image cache ────────────────────────────────────────────────────────────────
os.makedirs(CACHE_DIR, exist_ok=True)

DOWNLOAD_DELAY = 0.5   # secondes entre chaque téléchargement (BrickLink rate-limit)

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bricklink.com/",
    "Accept": "image/avif,image/webp,image/png,*/*",
}

def cached_image(item_id: str, color: str) -> tuple[str | None, bool]:
    """Return (local_path, downloaded) — downloaded=True only when a new request was made."""
    fname = f"{color}_{item_id}.png"
    fpath = os.path.join(CACHE_DIR, fname)
    if os.path.exists(fpath):
        return fpath, False
    url = f"https://img.bricklink.com/ItemImage/PN/{color}/{item_id}.png"
    try:
        req = urllib.request.Request(url, headers=_HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(fpath, "wb") as out:
                out.write(resp.read())
        time.sleep(DOWNLOAD_DELAY)
        return fpath, True
    except Exception as e:
        print(f"  ⚠  {item_id}/c{color}: {e}")
        return None, True   # True = a request was attempted, still sleep

# ── Part catalog ───────────────────────────────────────────────────────────────
part_names: dict[str, str] = {}
if os.path.exists(PARTS_CATALOG):
    for item in ET.parse(PARTS_CATALOG).getroot().findall("ITEM"):
        pid  = item.findtext("ITEMID", "").strip()
        name = item.findtext("ITEMNAME", "").strip()
        if pid and name:
            part_names[pid] = html_mod.unescape(name)

# ── Parse inventory ────────────────────────────────────────────────────────────
by_color: dict[str, list] = defaultdict(list)
total = 0
inv_root = ET.parse(INVENTORY_FILE).getroot()
all_items = [i for i in inv_root.findall("ITEM") if i.findtext("ITEMTYPE","").strip() == "P"]
n_total    = len(all_items)
n_cached   = sum(
    1 for i in all_items
    if os.path.exists(os.path.join(CACHE_DIR,
        f"{i.findtext('COLOR','0').strip()}_{i.findtext('ITEMID','').strip()}.png"))
)
n_download = n_total - n_cached
eta        = n_download * DOWNLOAD_DELAY
print(f"Images : {n_cached} en cache, {n_download} à télécharger (~{eta:.0f}s)")

def _progress(idx: int, n: int, n_dl: int, bar_width: int = 40) -> None:
    filled = int(bar_width * idx / n)
    bar    = "█" * filled + "░" * (bar_width - filled)
    sys.stdout.write(f"\r  [{bar}] {idx}/{n}  ({n_dl} téléchargées)")
    sys.stdout.flush()

n_downloaded = 0
for idx, item in enumerate(all_items, 1):
    item_id = item.findtext("ITEMID", "").strip()
    color   = item.findtext("COLOR", "0").strip()
    qty     = int(item.findtext("MINQTY", "1").strip())
    img, downloaded = cached_image(item_id, color)
    if downloaded:
        n_downloaded += 1
    name = part_names.get(item_id, "")
    by_color[color].append({"id": item_id, "color": color, "qty": qty, "img": img, "name": name})
    total += 1
    _progress(idx, n_total, n_downloaded)

print()  # newline after progress bar

# Sort colors by ID numerically, items within a color by part ID
sorted_colors = sorted(by_color.keys(), key=lambda c: int(c))
for c in sorted_colors:
    by_color[c].sort(key=lambda x: x["id"])

# ── HTML generation ────────────────────────────────────────────────────────────
def color_label(color_id: str) -> str:
    name = BRICKLINK_COLORS.get(color_id)
    return f"{name} (#{color_id})" if name else f"Couleur #{color_id}"

# Approximate hex for the color dot — verified against images
_DOT_COLORS = {
    # Solid
    "1":  "#ffffff", "2":  "#e4cd9e", "3":  "#f5cd2f", "4":  "#f7722e",
    "5":  "#c91a09", "6":  "#237841", "7":  "#1f69c0", "8":  "#583927",
    "9":  "#9ba19d", "10": "#484d48", "11": "#111111",
    "24": "#81007b", "25": "#f2a08c", "26": "#fcc9b3", "27": "#b52c20",
    "28": "#d09168", "29": "#c87c1e", "31": "#f8bb3d", "32": "#f0a06b",
    "33": "#f9f9a6", "34": "#bbd96e", "35": "#d9e4a7", "36": "#4bc93f",
    "37": "#58ab41", "38": "#c2dab8", "39": "#008080", "40": "#aadafd",
    "41": "#aee3d6", "42": "#6699cc", "43": "#8878a0", "44": "#c9cfe4",
    "47": "#c870a0", "48": "#708e7c", "49": "#e6e3da",
    "54": "#958a73", "55": "#7988a1", "58": "#b52c20", "59": "#720e0f",
    "62": "#b4d2e3", "63": "#063b7c",
    "66": "#d0d5d5", "68": "#a95500", "69": "#b28555",
    "71": "#de007f", "72": "#6db5d8", "73": "#9195ca", "76": "#aace3a",
    "80": "#184632", "83": "#f0f0f0", "85": "#575857", "86": "#afc0c4",
    "87": "#87ceeb", "88": "#7d3a28", "89": "#3d007b", "90": "#fbcba4",
    "91": "#c87c5c", "93": "#d3a5dc", "94": "#f39990", "95": "#898788",
    "96": "#ffd9a0", "97": "#4c61db", "99": "#e3f0f3",
    "103": "#f5e642", "104": "#f45197", "105": "#aadafd",
    "109": "#1a3a6a", "110": "#f9ba61",
    "115": "#dcbe61", "119": "#e8e8e8", "120": "#352100",
    "150": "#c87c5c", "152": "#c0eeea", "153": "#1498d7",
    "154": "#a5a5cb", "155": "#7c9051", "156": "#68aece",
    "157": "#ac78ba", "158": "#d9e47c", "161": "#c8a000",
    # Transparent (semi-transparent hex)
    "12": "#eeeeee", "13": "#6a3000aa", "14": "#0d69abaa",
    "15": "#aadafdaa", "16": "#37e86daa", "17": "#c91a09aa",
    "18": "#ff800daa", "19": "#f5cd2faa", "20": "#237841aa",
    # Chrome / Pearl
    "21": "#dcbe61", "22": "#c0c0c0", "52": "#6699ccaa",
    "57": "#7a6535", "64": "#2e8b2eaa", "82": "#e08080",
    "122": "#333333",
}

def _css_color(c: str) -> str:
    return _DOT_COLORS.get(c, "#ccc")

def piece_cell(p: dict) -> str:
    img_src = p["img"] if p["img"] else ""
    img_tag = (f'<img src="{img_src}" alt="{html_mod.escape(p["id"])}">'
               if img_src else '<span class="no-img">?</span>')
    name_tag = (f'<div class="part-name">{html_mod.escape(p["name"][:40])}</div>'
                if p["name"] else "")
    return f"""    <td class="piece">
      <div class="piece-inner">
        <div class="piece-img">{img_tag}</div>
        <div class="piece-meta">
          <span class="pid">{html_mod.escape(p["id"])}</span>
          <span class="qty-badge">×{p["qty"]}</span>
        </div>
        {name_tag}
        <div class="tally-area"></div>
      </div>
    </td>"""

sections = []
for color in sorted_colors:
    pieces = by_color[color]
    label  = color_label(color)
    color_total = sum(p["qty"] for p in pieces)
    header = (f'  <tr class="color-header">'
              f'<td colspan="{NUM_COLS}">'
              f'<span class="color-dot" style="background:{_css_color(color)}"></span>'
              f'{html_mod.escape(label)} — {len(pieces)} réf. / {color_total} pièces'
              f'</td></tr>')
    rows = []
    for i in range(0, len(pieces), NUM_COLS):
        chunk = pieces[i:i + NUM_COLS]
        cells = "".join(piece_cell(p) for p in chunk)
        cells += "    <td class='piece empty'></td>\n" * (NUM_COLS - len(chunk))
        rows.append(f"  <tr>\n{cells}  </tr>")
    sections.append(header + "\n" + "\n".join(rows))

col_width      = f"{100 // NUM_COLS}%"
col_tags       = "".join("<col>" for _ in range(NUM_COLS))
sections_html  = "\n".join(sections)

html_doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Inventaire LEGO 71395</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; font-size: 11px; background: #fff; color: #111; }}

  h1 {{ text-align: center; padding: 10px; font-size: 16px; border-bottom: 2px solid #333; }}
  .meta {{ text-align: center; color: #666; font-size: 10px; padding: 3px 0 6px; }}

  table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  col {{ width: {col_width}; }}

  /* ── Color group header ── */
  tr.color-header td {{
    background: #333;
    color: #fff;
    font-weight: bold;
    font-size: 11px;
    padding: 4px 8px;
    border-top: 6px solid #fff;
  }}
  .color-dot {{
    display: inline-block;
    width: 12px; height: 12px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.4);
    vertical-align: middle;
    margin-right: 5px;
  }}

  /* ── Piece cell ── */
  td.piece {{
    border: 1px solid #ccc;
    vertical-align: top;
    padding: 3px;
  }}
  td.piece.empty {{ border-color: transparent; }}
  .piece-inner {{ display: flex; flex-direction: column; align-items: center; height: 100%; }}

  .piece-img {{ height: 52px; display: flex; align-items: center; justify-content: center; }}
  .piece-img img {{ max-width: 70px; max-height: 52px; object-fit: contain; }}
  .no-img {{ font-size: 20px; color: #ccc; }}

  .piece-meta {{
    display: flex; align-items: baseline; justify-content: space-between;
    width: 100%; margin-top: 2px;
  }}
  .pid {{ font-weight: bold; font-size: 10px; }}
  .qty-badge {{
    background: #333; color: #fff;
    border-radius: 3px;
    padding: 0 4px;
    font-size: 11px; font-weight: bold;
  }}
  .part-name {{
    font-size: 9px; color: #666;
    text-align: center;
    width: 100%;
    margin-top: 1px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}

  /* ── Tally area (empty, for manual marks) ── */
  .tally-area {{
    width: 100%;
    margin-top: 3px;
    border: 1px solid #aaa;
    border-radius: 2px;
    min-height: 28px;
    flex: 1;
  }}

  /* ── Print ── */
  @media print {{
    @page {{ size: A4 portrait; margin: 10mm; }}
    body {{ font-size: 9px; }}
    h1 {{ font-size: 13px; padding: 6px; }}
    tr.color-header td {{ border-top-width: 4px; }}
    .piece-img {{ height: 44px; }}
    .piece-img img {{ max-width: 60px; max-height: 44px; }}
    .tally-area {{ min-height: 24px; }}
    td.piece {{ padding: 2px; }}
  }}
</style>
</head>
<body>
<h1>Inventaire LEGO 71395 — Super Mario 64</h1>
<p class="meta">{total} références — {len(sorted_colors)} couleurs — Généré le {date.today()}</p>
<table>
  {col_tags}
  <tbody>
{sections_html}
  </tbody>
</table>
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_doc)

print(f"\nGénéré : {OUTPUT_FILE}  ({total} pièces, {NUM_COLS} colonnes)")

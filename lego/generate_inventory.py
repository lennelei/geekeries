#!/usr/bin/env python3
"""Génère une fiche inventaire HTML imprimable d'un set LEGO.

L'inventaire vient de l'API Rebrickable (numéro de set, ex. 71395-1). Pièces et
couleurs sont ramenées aux ID BrickLink, qui servent aux images et à COLOR_ORDER.

Usage : python3 generate_inventory.py [--set 71395-1] [--refresh]
"""

import argparse
import csv
import json
import html as html_mod
import os, sys, time, urllib.request, urllib.error
from datetime import date
from collections import defaultdict, deque
from PIL import Image

import rebrickable

# ── Configuration ──────────────────────────────────────────────────────────────
_args = argparse.ArgumentParser(description=__doc__.splitlines()[0])
_args.add_argument("--set", default="71395-1", help="numéro de set Rebrickable (défaut : 71395-1)")
_args.add_argument("--refresh", action="store_true", help="réinterroger l'API au lieu du cache local")
ARGS = _args.parse_args()

SET_NUM        = ARGS.set if "-" in ARGS.set else f"{ARGS.set}-1"
SET_NUM_SHORT  = SET_NUM.removesuffix("-1")
OUTPUT_FILE    = f"{SET_NUM_SHORT}_inventory.html"
API_CACHE      = f"cache/api/{SET_NUM}.json"
CACHE_DIR      = "cache/images"
PROC_DIR       = "cache/processed"   # white-background-removed copies
NUM_COLS       = 3   # 3 or 4 columns of pieces per row on A4

# ── Ordre d'impression des couleurs ────────────────────────────────────────────
# Listez les IDs de couleur BrickLink (ceux du XML) dans l'ordre souhaité.
# "_" force un saut de page AVANT le groupe suivant.
# Les couleurs absentes de cette liste sont ajoutées à la fin (ordre numérique).
COLOR_ORDER = [
    "1",    # White
    "90",   # Light Nougat
    "3",    # Bright Yellow
    "2",    # Brick Yellow
    "_",
    "12",   # Transparent
    "150",  # Medium Nougat
    "85",   # Dark Stone Grey
    "_",
    "5",    # Bright Red
    "115",  # Warm Gold
    "69",   # Sand Yellow
    "120",  # Dark Brown
    "_",
    "86",   # Medium Stone Grey
    "_",
    "11",   # Black
    "4",    # Bright Orange
    "_",
    "88",   # Reddish Brown
    "68",   # Dark Orange
    "110",  # Flame Yellowish Orange
    "80",   # Earth Green
    "48",   # Sand Green
    "89",   # Medium Lilac
    "_",
    "7",    # Bright Blue
    "153",  # Dark Azur
    "15",   # Transparent Light Blue
    "42",   # Medium Blue
    "_",
    "152",  # Aqua
    "156",  # Medium Azure
    "104",  # Light Purple
    "34",   # Bright Yellowish Green
    "_",
    "6",    # Dark Green
    "36",   # Bright Green
]

# Couleurs : ID BrickLink → nom et numéro LEGO officiels + hex RGB.
# colors.csv est généré par fetch_colors.py depuis l'API Rebrickable.
COLORS_FILE = "colors.csv"
with open(COLORS_FILE, newline="") as _f:
    COLORS = {row["bl_id"]: row for row in csv.DictReader(_f)}

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

def download(url: str, fpath: str) -> tuple[str | None, bool]:
    """Return (local_path, downloaded) — downloaded=True only when a new request was made.
    Un contenu qui n'est pas une image (ex. page HTML d'erreur) n'est pas gardé."""
    if os.path.exists(fpath):
        return fpath, False
    try:
        req = urllib.request.Request(url, headers=_HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        with open(fpath, "wb") as out:
            out.write(data)
        with Image.open(fpath) as im:
            im.verify()
        return fpath, True
    except Exception as e:
        if os.path.exists(fpath):
            os.remove(fpath)
        print(f"\n  ⚠  {url} : {e}")
        return None, True   # True = a request was attempted, still sleep
    finally:
        time.sleep(DOWNLOAD_DELAY)

def cached_image(item: dict) -> tuple[str | None, bool]:
    """Image BrickLink (fond blanc, détourée ensuite) ; à défaut, photo Rebrickable."""
    item_id, color = item["id"], item["color"]
    ext = os.path.splitext(item.get("img_url") or "")[1] or ".jpg"
    rb_path = os.path.join(CACHE_DIR, f"rb_{color}_{item_id}{ext}")
    if os.path.exists(rb_path):   # repli déjà en cache : ne pas réessayer BrickLink
        return rb_path, False
    path, dl = download(f"https://img.bricklink.com/ItemImage/PN/{color}/{item_id}.png",
                        os.path.join(CACHE_DIR, f"{color}_{item_id}.png"))
    if path or not item.get("img_url"):
        return path, dl
    path, dl2 = download(item["img_url"], rb_path)
    return path, dl or dl2

os.makedirs(PROC_DIR, exist_ok=True)

def processed_image(src_path: str, fname: str) -> str:
    """Return path to a version of the image with white background made transparent.
    Result is cached in PROC_DIR; flood-fills from all 4 corners."""
    dst = os.path.join(PROC_DIR, fname)
    if os.path.exists(dst):
        return dst
    img = Image.open(src_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size
    tol = 4  # BrickLink background is pure white — keep tolerance very tight

    def is_bg(x, y):
        r, g, b, a = pixels[x, y]
        return r >= 255 - tol and g >= 255 - tol and b >= 255 - tol

    visited = [[False] * w for _ in range(h)]
    q = deque()
    for cx, cy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if is_bg(cx, cy) and not visited[cy][cx]:
            visited[cy][cx] = True
            q.append((cx, cy))

    while q:
        x, y = q.popleft()
        pixels[x, y] = (255, 255, 255, 0)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and is_bg(nx, ny):
                visited[ny][nx] = True
                q.append((nx, ny))

    img.save(dst, "PNG")
    return dst

# ── Inventaire (API Rebrickable, mis en cache localement) ──────────────────────
def load_set() -> dict:
    """Infos du set + liste de ses pièces, depuis le cache ou l'API."""
    if os.path.exists(API_CACHE) and not ARGS.refresh:
        with open(API_CACHE) as f:
            return json.load(f)
    print(f"Interrogation de Rebrickable pour {SET_NUM}…")
    data = {
        "set": rebrickable.get(f"sets/{SET_NUM}/"),
        "parts": rebrickable.get_all(f"sets/{SET_NUM}/parts/"),
    }
    os.makedirs(os.path.dirname(API_CACHE), exist_ok=True)
    with open(API_CACHE, "w") as f:
        json.dump(data, f)
    return data

# Repli si la couleur n'a pas d'ID BrickLink dans la réponse : via colors.csv
_RB_TO_BL = {}
for _bl_id, _c in COLORS.items():
    _RB_TO_BL.setdefault(_c["rebrickable_id"], _bl_id)

def bl_color(color: dict) -> str:
    bl = (color.get("external_ids") or {}).get("BrickLink")
    if bl and bl.get("ext_ids"):
        return str(bl["ext_ids"][0])
    return _RB_TO_BL.get(str(color["id"]), f"rb{color['id']}")

def bl_part(part: dict) -> str:
    bl = part["external_ids"].get("BrickLink") or []
    return part["part_num"] if part["part_num"] in bl or not bl else bl[0]

set_data = load_set()
SET_INFO = set_data["set"]

# Regroupe par (pièce, couleur) BrickLink ; les pièces de rechange sont exclues
items: dict[tuple[str, str], dict] = {}
for line in set_data["parts"]:
    if line["is_spare"]:
        continue
    key = (bl_part(line["part"]), bl_color(line["color"]))
    it = items.setdefault(key, {"id": key[0], "color": key[1], "qty": 0,
                                "name": line["part"]["name"], "elements": [],
                                "img_url": line["part"]["part_img_url"]})
    it["qty"] += line["quantity"]
    if line.get("element_id") and line["element_id"] not in it["elements"]:
        it["elements"].append(line["element_id"])
all_items = list(items.values())

# ── Images ─────────────────────────────────────────────────────────────────────
by_color: dict[str, list] = defaultdict(list)
total = 0
n_total    = len(all_items)
n_cached   = sum(
    1 for i in all_items
    if os.path.exists(os.path.join(CACHE_DIR, f"{i['color']}_{i['id']}.png"))
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
    item_id, color = item["id"], item["color"]
    img, downloaded = cached_image(item)
    if downloaded:
        n_downloaded += 1
    fname = f"{color}_{item_id}.png"
    # Seules les PNG BrickLink (fond blanc pur) sont détourées ; la photo de repli reste telle quelle
    item["img"] = (processed_image(img, fname) if img.endswith(".png") else img) if img else None
    by_color[color].append(item)
    total += 1
    _progress(idx, n_total, n_downloaded)

print()  # newline after progress bar

# Sort colors by ID numerically, items within a color by part ID
sorted_colors = sorted(by_color.keys(), key=lambda c: (not c.isdigit(), int(c) if c.isdigit() else 0, c))
for c in sorted_colors:
    by_color[c].sort(key=lambda x: x["id"])

# ── HTML generation ────────────────────────────────────────────────────────────
def color_label(color_id: str) -> str:
    c = COLORS.get(color_id)
    if not c:
        return f"Couleur #{color_id}"
    if c["lego_name"]:
        return f'{c["lego_name"]} (LEGO {c["lego_id"]} / BL {color_id})'
    return f'{c["bl_name"]} (BL {color_id})'

def _css_color(color_id: str) -> str:
    c = COLORS.get(color_id)
    if not c:
        return "#ccc"
    # Couleurs transparentes : pastille semi-opaque
    return f'#{c["rgb"]}' + ("aa" if c["is_trans"] == "1" else "")

def piece_cell(p: dict) -> str:
    img_src = p["img"] if p["img"] else ""
    img_tag = (f'<img src="{img_src}" alt="{html_mod.escape(p["id"])}">'
               if img_src else '<span class="no-img">?</span>')
    name_text = html_mod.escape(p["name"]) if p["name"] else ""
    # N° d'élément LEGO (pièce + couleur), celui qui sert à commander chez LEGO
    elt_html = (f'<span class="pg-elt">{html_mod.escape(p["elements"][0])}</span>'
                if p.get("elements") else "")
    return f"""    <td class="piece">
      <div class="piece-grid">
        <div class="pg-img">{img_tag}</div>
        <div class="pg-name"><span class="pg-name-text">{name_text}</span><span class="qty-badge">×{p["qty"]}</span></div>
        <div class="pg-ref" title="Réf. BrickLink / n° d'élément LEGO">{html_mod.escape(p["id"])}{elt_html}</div>
        <div class="pg-tally"></div>
      </div>
    </td>"""

# ── Résoudre l'ordre et les sauts de page ──────────────────────────────────────
page_break_before: set[str] = set()
ordered_colors: list[str] = []
next_is_break = False
for entry in COLOR_ORDER:
    if entry == "_":
        next_is_break = True
    elif entry in by_color:
        ordered_colors.append(entry)
        if next_is_break:
            page_break_before.add(entry)
            next_is_break = False

# Couleurs absentes du COLOR_ORDER → fin, ordre numérique
listed = set(ordered_colors)
for c in sorted_colors:
    if c not in listed:
        ordered_colors.append(c)

def build_large_section(color, pieces, add_page_break):
    label = color_label(color)
    color_total = sum(p["qty"] for p in pieces)
    extra = " page-break" if add_page_break else ""
    header = (f'  <tr class="color-header{extra}">'
              f'<td colspan="{NUM_COLS}">'
              f'<span class="color-dot" style="background:{_css_color(color)}"></span>'
              f'{html_mod.escape(label)} — {len(pieces)} réf. / {color_total} pièces'
              f'</td></tr>')
    rows = []
    for i in range(0, len(pieces), NUM_COLS):
        chunk = pieces[i:i + NUM_COLS]
        cells = "".join(piece_cell(p) for p in chunk)
        cells += "    <td class='piece empty'></td>\n" * (NUM_COLS - len(chunk))
        rows.append(f"  <tr class='piece-row'>\n{cells}  </tr>")
    return header + "\n" + "\n".join(rows)

def build_packed_section(groups, add_page_break):
    """Render several small color groups side-by-side on a single piece row."""
    total = sum(len(ps) for _, ps in groups)
    padding = NUM_COLS - total
    extra = " page-break" if add_page_break else ""

    # Header row: one <td> per color group, colspan = number of pieces
    hcells = []
    for color, ps in groups:
        label = color_label(color)
        color_total = sum(p["qty"] for p in ps)
        n = len(ps)
        hcells.append(
            f'<td colspan="{n}" class="mini-color-header">'
            f'<span class="color-dot" style="background:{_css_color(color)}"></span>'
            f'{html_mod.escape(label)} — {n} réf. / {color_total} pièces'
            f'</td>'
        )
    if padding > 0:
        hcells.append(f'<td colspan="{padding}" class="mini-color-header empty"></td>')
    header = f'  <tr class="mini-header-row{extra}">{"".join(hcells)}</tr>'

    # Single piece row: all pieces from all groups
    cells = ""
    for color, ps in groups:
        cells += "".join(piece_cell(p) for p in ps)
    cells += "    <td class='piece empty'></td>\n" * padding
    piece_row = f"  <tr class='piece-row'>\n{cells}  </tr>"

    return header + "\n" + piece_row

sections = []
pending_groups: list = []   # [(color, pieces), ...]
pending_cols   = 0
pending_break  = False

def flush_pending():
    global pending_groups, pending_cols, pending_break
    if not pending_groups:
        return
    sections.append(build_packed_section(pending_groups, pending_break))
    pending_groups = []
    pending_cols   = 0
    pending_break  = False

for color in ordered_colors:
    pieces = by_color[color]
    pieces.sort(key=lambda x: (
        (0, x["name"].lower(), x["id"]) if x["name"] else (1, x["id"], "")
    ))
    add_break = color in page_break_before

    if len(pieces) >= NUM_COLS:
        # Large section: flush any pending small groups first
        flush_pending()
        sections.append(build_large_section(color, pieces, add_break))
    else:
        # Small section: pack into a shared row
        if add_break and pending_groups:
            # Page break forces a new packed row
            flush_pending()
        if pending_cols + len(pieces) > NUM_COLS:
            # No more room in current packed row
            flush_pending()
        if not pending_groups and add_break:
            pending_break = True
        pending_groups.append((color, pieces))
        pending_cols += len(pieces)

flush_pending()

col_width      = f"{100 // NUM_COLS}%"
col_tags       = "".join("<col>" for _ in range(NUM_COLS))
sections_html  = "\n".join(sections)

html_doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Inventaire LEGO {SET_NUM_SHORT}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; font-size: 11px; background: #fff; color: #111; }}

  h1 {{ text-align: center; padding: 10px; font-size: 16px; border-bottom: 2px solid #333; }}
  .meta {{ text-align: center; color: #666; font-size: 10px; padding: 3px 0 6px; }}

  table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  col {{ width: {col_width}; }}

  /* ── Color group header (large) ── */
  tr.color-header.page-break td {{
    break-before: page;
  }}
  tr.color-header td {{
    font-weight: bold;
    font-size: 11px;
    padding: 4px 8px;
    border-top: 6px solid #000;
  }}

  /* ── Compact (small) color group headers ── */
  tr.mini-header-row.page-break {{
    break-before: page;
  }}
  tr.mini-header-row td.mini-color-header {{
    font-weight: bold;
    font-size: 10px;
    padding: 3px 6px;
    border-top: 6px solid #000;
    border-right: 2px solid #888;
  }}
  tr.mini-header-row td.mini-color-header:last-child {{
    border-right: none;
  }}
  tr.mini-header-row td.mini-color-header.empty {{
    border-top: 6px solid #000;
    border-right: none;
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
    padding: 2px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  td.piece.empty {{ border-color: transparent; visibility: hidden; }}

  /* Inner grid — 2 cols × 3 rows, on a div so table columns stay intact
     col1: image (rows 1-2) + ref (row 3)
     col2: nom+nb (row 1) + comptage (rows 2-3)              */
  .piece-grid {{
    display: grid;
    grid-template-columns: 58px 1fr;
    grid-template-rows: auto 1fr auto;
    grid-template-areas: "img name" "img tally" "ref tally";
    min-height: 80px;
    height: 100%;
  }}

  .pg-img {{
    grid-area: img;
    display: flex; align-items: center; justify-content: center;
    padding: 2px;
    background: #ffffff;
    border-radius: 2px;
  }}
  .pg-img img {{ max-width: 54px; max-height: 56px; object-fit: contain; }}
  .no-img {{ font-size: 18px; color: #ccc; }}

  .pg-name {{
    grid-area: name;
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 3px; padding: 2px 2px 2px 4px;
    font-size: 9px; line-height: 1.3;
  }}
  .pg-name-text {{
    flex: 1;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }}
  .qty-badge {{
    background: #fff;
    color: #111;
    border: 1.5px solid #333;
    border-radius: 3px;
    padding: 0 4px;
    font-size: 11px; font-weight: bold;
    white-space: nowrap; flex-shrink: 0;
    align-self: flex-start;
  }}

  .pg-ref {{
    grid-area: ref;
    font-size: 8px; font-weight: bold; color: #777;
    text-align: center; align-self: center;
    padding: 2px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  .pg-elt {{ display: block; font-weight: normal; color: #999; }}

  .pg-tally {{
    grid-area: tally;
    border: 1px solid #bbb;
    border-radius: 2px;
    margin: 2px 2px 2px 3px;
  }}

  /* ── Prevent rows from splitting across pages ── */
  tr.piece-row {{
    break-inside: avoid;
    page-break-inside: avoid;
  }}

  /* ── Print ── */
  @media print {{
    @page {{ size: A4 portrait; margin: 10mm; }}
    body {{ font-size: 9px; }}
    h1 {{ font-size: 13px; padding: 6px; }}
    tr.color-header td {{ border-top-width: 4px; }}
    .piece-grid {{ min-height: 72px; }}
    .pg-img img {{ max-width: 48px; max-height: 50px; }}
  }}
</style>
</head>
<body>
<h1>Inventaire LEGO {SET_NUM_SHORT} — {html_mod.escape(SET_INFO["name"])}</h1>
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

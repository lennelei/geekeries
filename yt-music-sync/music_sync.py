import os, re, sys, yaml, json, yt_dlp, argparse, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

# --- LOGS & UTILS ---
class YtdlpLogger:
    def debug(self, m): pass
    def warning(self, m): pass
    def error(self, m): pass

def clean_string(t):
    return ' '.join(re.sub(r'[\\/*?:"<>|]', '', t or "Inconnu").split())

def generate_m3u(directory, playlist_name):
    mp3_files = sorted([f for f in os.listdir(directory) if f.endswith('.mp3')])
    m3u_path = os.path.join(directory, f"00_playlist_{playlist_name}.m3u")
    with open(m3u_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for mp3 in mp3_files:
            f.write(f"{mp3}\n")
    return m3u_path

# --- LOGIQUE DE RÉCUPÉRATION ---

def get_playlist_items(source, cookies_file=None, overrides=None):
    overrides = overrides or {}
    items = []
    
    # --- CAS 1 : PLAYLIST YOUTUBE (URL) ---
    if source.startswith('http'):
        ydl_opts = {
            'flat_playlist': True, 'quiet': True, 'extract_flat': True,
            'cookiefile': cookies_file if cookies_file and os.path.exists(cookies_file) else None
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source, download=False)
            if 'entries' in info:
                for idx, e in enumerate(info['entries'], start=1):
                    orig_id = e['id']
                    final_query = overrides.get(orig_id, f"https://www.youtube.com/watch?v={orig_id}")
                    items.append({
                        'id': orig_id, 
                        'index': idx, 
                        'title': e.get('title', 'Inconnu'),
                        'query': final_query,
                        'is_override': orig_id in overrides
                    })

    # --- CAS 2 : SOURCE CSV (Fichier Local) ---
    elif source.endswith('.csv'):
        if not os.path.exists(source):
            print(f" ⚠ Fichier {source} introuvable.")
            return []
            
        with open(source, 'r', encoding='utf-8-sig') as f:
            for idx, line in enumerate(f, start=1):
                query = line.strip()
                if not query: continue
                
                # On essaie d'extraire un ID YouTube si c'est une URL
                vid_id = None
                if 'youtube.com' in query or 'youtu.be' in query:
                    # Regex pour capturer l'ID de 11 caractères
                    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', query)
                    if match: vid_id = match.group(1)
                
                # Si pas d'ID YouTube, on génère un ID court basé sur le texte
                cid = vid_id if vid_id else re.sub(r'\W+', '', query)[:20]
                
                items.append({
                    'id': cid,
                    'index': idx,
                    'title': query, # Sera remplacé par le vrai titre au téléchargement
                    'query': query,
                    'is_override': False
                })
                
    return items

def process_item(item, output_dir, quality, cookies_file=None):
    prefix = str(item['index']).zfill(3)
    base_ydl_opts = {
        'format': 'ba/b', 'logger': YtdlpLogger(), 'quiet': True, 'no_warnings': True,
        'cookiefile': cookies_file if cookies_file and os.path.exists(cookies_file) else None,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web'], 'skip': ['dash', 'hls']}},
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality}],
    }

    try:
        temp_pattern = os.path.join(output_dir, f"temp_{item['id']}")
        ydl_opts = {**base_ydl_opts, 'outtmpl': f"{temp_pattern}.%(ext)s"}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(item['query'], download=True)
            except Exception as e:
                # Fallback recherche (seulement si ce n'est pas un override manuel)
                if not item.get('is_override') and item['query'].startswith('http'):
                    tqdm.write(f" 🔄 Fallback recherche pour '{item['title']}'...")
                    search_query = f"ytsearch1:{item['title']} audio"
                    info = ydl.extract_info(search_query, download=True)
                    if 'entries' in info: info = info['entries'][0]
                else:
                    raise e

        time.sleep(1.2)
        found = [f for f in os.listdir(output_dir) if f.startswith(f"temp_{item['id']}") and f.endswith('.mp3')]
        if not found: raise Exception("MP3 non trouvé")

        temp_path = os.path.join(output_dir, found[0])
        audio = MP3(temp_path, ID3=EasyID3)
        raw_t, uploader = info.get('title', 'Inconnu'), info.get('uploader', 'Inconnu')
        artist, title = (raw_t.split(" - ", 1)) if " - " in raw_t else (uploader, raw_t)
        
        audio['artist'], audio['title'], audio['tracknumber'] = clean_string(artist), clean_string(title), str(item['index'])
        audio.save()

        final_filename = f"{prefix} - {clean_string(artist)} - {clean_string(title)}.mp3"
        os.replace(temp_path, os.path.join(output_dir, final_filename))
        return item['id'], "ok", final_filename, f" ✔ {prefix} | {item['title']}"

    except Exception as e:
        return item['id'], "ko", None, f" ⚠ {prefix} | {item['title']} -> {str(e).splitlines()[0]}"

def sync_playlist(name, data, global_config):
    out_dir = os.path.join(global_config['output_dir'], name)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    state_file = f"data/{name}_state.json"
    state = json.load(open(state_file)) if os.path.exists(state_file) else {}
    c_file = global_config.get('cookies_file')

    print(f"\n🔄 Sync Miroir (+ Overrides) : {name}")
    current_items = get_playlist_items(data['url'], c_file, data.get('overrides'))

    # 1. NETTOYAGE
    current_ids = {i['id'] for i in current_items}
    for sid in list(state.keys()):
        if sid not in current_ids:
            if state[sid].get('filename'):
                p = os.path.join(out_dir, state[sid]['filename'])
                if os.path.exists(p): os.remove(p)
            del state[sid]

    # 2. SMART RENAME (Gestion du décalage)
    for item in current_items:
        item_id = item['id']
        if item_id in state and state[item_id].get('status') == "ok":
            old_fn = state[item_id].get('filename')
            if not old_fn: continue
            
            prefix = str(item['index']).zfill(3)
            # Reconstruct nouveau nom (format: INDEX - RESTE)
            name_part = old_fn.split(" - ", 1)[-1] if " - " in old_fn else old_fn
            new_fn = f"{prefix} - {name_part}"
            
            if old_fn != new_fn:
                old_p, new_p = os.path.join(out_dir, old_fn), os.path.join(out_dir, new_fn)
                if os.path.exists(old_p):
                    os.rename(old_p, new_p)
                    state[item_id].update({'index': item['index'], 'filename': new_fn})
                    try:
                        audio = MP3(new_p, ID3=EasyID3)
                        audio['tracknumber'] = str(item['index'])
                        audio.save()
                    except: pass

    # 3. TÉLÉCHARGEMENT (Version améliorée avec détection de changement de source)
    to_dl = []
    for item in current_items:
        item_id = item['id']
        current_query = item['query']
        
        # On télécharge si :
        # - L'ID n'est pas dans le state
        # - OU le statut n'est pas "ok"
        # - OU l'URL actuelle est différente de l'URL précédemment utilisée (Override ajouté ou changé)
        old_state = state.get(item_id, {})
        if old_state.get('status') != "ok" or old_state.get('source_url') != current_query:
            
            # Si c'est un changement d'URL, on supprime l'ancien fichier pour éviter les doublons
            if old_state.get('source_url') and old_state.get('source_url') != current_query:
                if old_state.get('filename'):
                    old_p = os.path.join(out_dir, old_state['filename'])
                    if os.path.exists(old_p):
                        os.remove(old_p)
                        tqdm.write(f" ♻️  Source modifiée pour [{item_id}], re-téléchargement...")
            
            to_dl.append(item)

    if to_dl:
        with ThreadPoolExecutor(max_workers=global_config['max_workers']) as exe:
            futures = {exe.submit(process_item, i, out_dir, global_config.get('audio_quality', '192'), c_file): i for i in to_dl}
            # Dans la boucle de résultat des threads :
            for f in tqdm(as_completed(futures), total=len(to_dl), unit="mp3"):
                iid, status, fname, msg = f.result()
                
                # On retrouve l'item pour avoir son URL (query)
                item_obj = next(i for i in current_items if i['id'] == iid)
                
                state[iid] = {
                    "status": status, 
                    "index": item_obj['index'], 
                    "filename": fname, 
                    "source_url": item_obj['query'], # <--- On stocke l'URL utilisée ici
                    "error": msg if status == "ko" else None
                }
                tqdm.write(msg)
    else:
        print(" ✨ Fichiers à jour.")

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    generate_m3u(out_dir, name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist", "-p")
    args = parser.parse_args()

    with open("playlists.yaml", 'r', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
    
    pls = conf.get('playlists', {})
    if args.playlist and args.playlist in pls:
        sync_playlist(args.playlist, pls[args.playlist], conf['config'])
    else:
        for n, d in pls.items(): sync_playlist(n, d, conf['config'])
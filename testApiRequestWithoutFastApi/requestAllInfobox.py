import requests
import re
import time
import os

"""
Récupération des infobox Tolkien Gateway

Ce script interroge l’API MediaWiki de tolkiengateway.net pour :
- lister des pages (via `allpages`),
- récupérer le wikitext de chaque page (`parse`),
- extraire l’infobox (bloc {{Infobox ... }} avec gestion des accolades imbriquées),
- enregistrer chaque infobox dans le dossier `infoboxes/` avec un nom de fichier sûr pour Windows,
- consigner un journal d’état dans `infoboxes/infobox_log.txt`.

Fonctions principales
- `safe_filename_from_title(title, max_length=180)`: normalise les titres en noms de fichiers valides Windows (remplace caractères interdits, gère noms réservés, tronque).
- `get_infobox_wikitext(page_title)`: récupère le wikitext brut d’une page via `action=parse`.
- `extract_infobox(wikitext)`: isole l’infobox en comptant les `{{` / `}}` pour couvrir l’imbrication.
- `get_all_page_titles(limit=500)`: pagine sur `list=allpages` pour collecter des titres (le script utilise `limit=50` par défaut).
- `get_all_infobox_template_titles(limit=500)`: (optionnel) liste les modèles d’infobox via la catégorie `Infobox_templates`.

Entrées/Sorties
- Entrée: aucune entrée utilisateur (paramètre `limit` codé en dur, modifiable).
- Sorties: fichiers `infobox_*.txt` dans `infoboxes/` + `infobox_log.txt` (OK / NO INFOBOX / NO WIKITEXT).

Prérequis
- Python 3.8+ et le paquet `requests`.
- Installer les dépendances: `pip install -r requirements.txt` (ou `pip install requests`).

Utilisation
- Exécuter: `python testApiRequest/requestAllInfobox.py`
- Adapter `limit` si nécessaire (plus grand = plus de pages = plus lent).
- Respect du site: le script utilise un `User-Agent` et traite séquentiellement; ajouter un `time.sleep()` si vous augmentez fortement `limit`.

Notes
- Les noms de fichiers sont nettoyés pour éviter les erreurs Windows (caractères interdits, noms réservés comme CON/PRN, espaces/points en fin).
- L’extraction de l’infobox tient compte des accolades imbriquées; si aucune infobox n’est trouvée, le journal note `NO INFOBOX`.
- En cas d’erreur HTTP, le script affiche le code et un extrait de réponse.
"""

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

API = "https://tolkiengateway.net/w/api.php"


def safe_filename_from_title(title: str, max_length: int = 180) -> str:
    """Create a Windows-safe filename stem from a wiki page title."""
    stem = re.sub(r"\s+", "_", title.strip())

    stem = re.sub(r"[<>:\\'/\\|\\?\\*]", "_", stem)

    stem = "".join(ch for ch in stem if ord(ch) >= 32)

    stem = stem.strip(" .")

    if not stem:
        stem = "untitled"
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        stem = f"_{stem}_"

    if len(stem) > max_length:
        stem = stem[:max_length].rstrip(" ._")
        if not stem:
            stem = "untitled"

    return stem

def get_infobox_wikitext(page_title):
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    resp = requests.get(API, params=params, headers=headers)
    if resp.status_code != 200:
        print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
        return None
    data = resp.json()
    if "parse" in data and "wikitext" in data["parse"]:
        return data["parse"]["wikitext"]["*"]
    else:
        print("No wikitext found in response:", data)
        return None
    
def extract_infobox(wikitext):
    start = wikitext.lower().find('{{infobox')
    if start == -1:
        #print("No infobox found.")
        return None
    count = 0
    for i in range(start, len(wikitext)):
        if wikitext[i:i+2] == '{{':
            count += 1
        elif wikitext[i:i+2] == '}}':
            count -= 1
            if count == 0:
                return wikitext[start:i+2]
    print("No complete infobox found.")
    return None


def get_all_page_titles(limit=500):
    API = "https://tolkiengateway.net/w/api.php"
    params = {
        "action": "query",
        "list": "allpages",
        "format": "json",
        "aplimit": limit
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    titles = []
    cont = {}
    while True:
        params.update(cont)
        resp = requests.get(API, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        data = resp.json()
        if "query" in data and "allpages" in data["query"]:
            titles.extend([p["title"] for p in data["query"]["allpages"]])
        else:
            print("Unexpected response structure:", data)
            break
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    return titles


def get_all_infobox_template_titles(limit=500):
    titles = []
    cont = {}
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Infobox_templates",
            "cmlimit": limit,
            "format": "json"
        }
        params.update(cont)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
        }

        resp = requests.get(API, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}")
            break

        data = resp.json()
        if "query" in data and "categorymembers" in data["query"]:
            for p in data["query"]["categorymembers"]:
                titles.append(p["title"])
        else:
            break

        if "continue" in data:
            cont = data["continue"]
        else:
            break

    return titles


output_dir = "infoboxes"
os.makedirs(output_dir, exist_ok=True)

start_time = time.time()
all_titles = get_all_page_titles(limit=50)
log_file = os.path.join(output_dir, "infobox_log.txt")
with open(log_file, "w", encoding="utf-8") as log:
    for idx, title in enumerate(all_titles, 1):
        print(f"Processing {idx}/{len(all_titles)}: {title}")
        wikitext = get_infobox_wikitext(title)
        if wikitext:
            infobox = extract_infobox(wikitext)
            if infobox:
                base = safe_filename_from_title(title)
                filename = os.path.join(output_dir, f"infobox_{base}.txt")

                if os.path.exists(filename):
                    suffix = 2
                    while True:
                        candidate = os.path.join(output_dir, f"infobox_{base}_{suffix}.txt")
                        if not os.path.exists(candidate):
                            filename = candidate
                            break
                        suffix += 1

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"--- {title} ---\n{infobox}\n")
                print(f"Saved infobox for '{title}' to {filename}")
                log.write(f"OK: {idx}: {title} -> {os.path.basename(filename)}\n")
            else:
                print(f"No infobox found for '{title}'")
                log.write(f"NO INFOBOX: {idx}: {title}\n")
        else:
            print(f"No wikitext found for '{title}'")
            log.write(f"NO WIKITEXT: {idx}: {title}\n")
end_time = time.time()
print(f"Finished processing {len(all_titles)} pages in {end_time - start_time:.2f} seconds.")
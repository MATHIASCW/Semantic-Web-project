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

    stem = re.sub(r'[<>:"/\\|\\?\\*]', "_", stem)

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


def extract_section(wikitext, section_title="Other names"):
    """
    Extrait le contenu d'une section wikitext (par exemple ==Other names==).
    Retourne None si la section n'est pas trouvée.
    """
    pattern = rf"^==\s*{re.escape(section_title)}\s*==\s*(.*?)(?=^==[^=]|\Z)"
    match = re.search(pattern, wikitext, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def get_existing_titles_from_infoboxes(output_dir="infoboxes"):
    """
    Récupère les titres de pages déjà téléchargées.
    Extrait le titre depuis la première ligne: --- Page Title ---
    Utile pour le mode incrémental.
    """
    existing_titles = set()
    
    if not os.path.exists(output_dir):
        return existing_titles
    
    for filename in os.listdir(output_dir):
        if filename.startswith("infobox_") and filename.endswith(".txt"):
            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    match = re.match(r"^---\s+(.+?)\s+---$", first_line)
                    if match:
                        existing_titles.add(match.group(1))
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return existing_titles


def get_pages_from_category(category_name="Category:Characters", limit=500):
    """
    Récupère les pages d'une catégorie spécifique.
    Très efficace pour cibler un type de contenu (ex: personnages).
    """
    API = "https://tolkiengateway.net/w/api.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    
    titles = []
    cont = {}
    
    print(f"Fetching pages from {category_name}...")
    
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_name,
            "cmlimit": limit,
            "cmnamespace": 0,  
            "format": "json"
        }
        params.update(cont)
        
        resp = requests.get(API, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        
        data = resp.json()
        if "query" in data and "categorymembers" in data["query"]:
            for page in data["query"]["categorymembers"]:
                titles.append(page["title"])
        else:
            print("Unexpected response structure:", data)
            break
        
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    
    return titles


def get_pages_with_infobox(limit=500):
    """
    Récupère les pages qui utilisent les templates d'infobox.
    Plus efficace que de récupérer toutes les pages.
    """
    API = "https://tolkiengateway.net/w/api.php"
    
    
    infobox_templates = [
        "Template:Actor",
        "Template:Album",
        "Template:Amonhen",
        "Template:Arnorian infobox",
        "Template:Artist infobox",
        "Template:Audiobook infobox",
        "Template:Author infobox",
        "Template:Avar infobox",
        "Template:Band",
        "Template:Battle",
        "Template:Beyondbree",
        "Template:Board game infobox",
        "Template:Book",
        "Template:Campaign",
        "Template:Chapter",
        "Template:Collectible",
        "Template:Collectible card",
        "Template:Company infobox",
        "Template:Convention",
        "Template:Director",
        "Template:Dragon infobox",
        "Template:Druadan infobox",
        "Template:Dwarves infobox",
        "Template:Eagle infobox",
        "Template:Easterling infobox",
        "Template:Edain infobox",
        "Template:Elves infobox",
        "Template:Ent infobox",
        "Template:Episode infobox",
        "Template:Events",
        "Template:Evil infobox",
        "Template:Film infobox",
        "Template:Gondorian infobox",
        "Template:Half-elf infobox",
        "Template:Infobox character",
        "Template:Infoboxes",
        "Template:Journal",
        "Template:Kingdom",
        "Template:Letter infobox",
        "Template:Location infobox",
        "Template:Maiar infobox",
        "Template:Mallorn",
        "Template:Men infobox",
        "Template:Modernpeople infobox",
        "Template:Mountain",
        "Template:Mythlore",
        "Template:Nandor infobox",
        "Template:Noble House infobox",
        "Template:Noldor infobox",
        "Template:Northmen infobox",
        "Template:Numenorean infobox",
        "Template:Object infobox",
        "Template:Organization infobox",
        "Template:Other infobox",
        "Template:People infobox",
        "Template:Person infobox",
        "Template:Plant infobox",
        "Template:Poem infobox",
        "Template:Puzzle infobox",
        "Template:Race infobox",
        "Template:Rohirrim infobox",
        "Template:Scene",
        "Template:SEVEN",
        "Template:Sindar infobox",
        "Template:Song",
        "Template:User infobox",
        "Template:Valar infobox",
        "Template:Vanyar infobox",
        "Template:Video game infobox",
        "Template:VTbox",
        "Template:War",
        "Template:Website",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    
    all_titles = set() 
    
    for template in infobox_templates:
        print(f"Fetching pages using {template}...")
        params = {
            "action": "query",
            "list": "embeddedin",
            "eititle": template,
            "eilimit": limit,
            "einamespace": 0,
            "format": "json"
        }
        
        cont = {}
        while True:
            params.update(cont)
            resp = requests.get(API, params=params, headers=headers)
            if resp.status_code != 200:
                print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
                break
            
            data = resp.json()
            if "query" in data and "embeddedin" in data["query"]:
                for page in data["query"]["embeddedin"]:
                    all_titles.add(page["title"])
            else:
                print(f"Unexpected response for {template}:", data)
                break
            
            if "continue" in data:
                cont = data["continue"]
            else:
                break
        
        time.sleep(0.5)
    
    return list(all_titles)


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

MODE = 2  
INCREMENTAL = True 
start_time = time.time()

if MODE == 1:
    print("MODE 1: Récupération depuis la catégorie Characters...")
    all_titles = get_pages_from_category("Category:Characters", limit=500)
elif MODE == 2:
    print("MODE 2: Récupération des pages avec templates d'infobox...")
    all_titles = get_pages_with_infobox(limit=500)
else:
    print("MODE 3: Récupération de toutes les pages (non recommandé)...")
    all_titles = get_all_page_titles(limit=50)

if INCREMENTAL:
    existing_titles = get_existing_titles_from_infoboxes(output_dir)
    initial_count = len(all_titles)
    all_titles = [t for t in all_titles if t not in existing_titles]
    skipped_count = initial_count - len(all_titles)
    print(f"Mode incrémental activé:")
    print(f"  • Pages à traiter initialement: {initial_count}")
    print(f"  • Pages déjà téléchargées:     {skipped_count}")
    print(f"  • Pages à télécharger:         {len(all_titles)}")
else:
    print("Mode incrémental désactivé: toutes les pages seront traitées")

print(f"Found {len(all_titles)} pages to process.")

log_file = os.path.join(output_dir, "infobox_log.txt")
with open(log_file, "a", encoding="utf-8") as log: 
    log.write(f"\n\n===== Session started at {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
    log.write(f"Mode: {MODE}, Incremental: {INCREMENTAL}\n")
    
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

                other_names_section = extract_section(wikitext, "Other names")

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"--- {title} ---\n{infobox}\n")
                    if other_names_section:
                        f.write("\n--- Other names (section) ---\n")
                        f.write(other_names_section)
                        f.write("\n")
                print(f"Saved infobox for '{title}' to {filename}")
                log.write(f"OK: {title} -> {os.path.basename(filename)}\n")
            else:
                print(f"No infobox found for '{title}'")
                log.write(f"NO INFOBOX: {title}\n")
        else:
            print(f"No wikitext found for '{title}'")
            log.write(f"NO WIKITEXT: {title}\n")
    
    end_time = time.time()
    duration = end_time - start_time
    log.write(f"Session completed in {duration:.2f} seconds\n")

print(f"Finished processing {len(all_titles)} pages in {end_time - start_time:.2f} seconds.")
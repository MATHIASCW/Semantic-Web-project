import requests
import re
import time
import os

"""
Fetch Tolkien Gateway infoboxes

This script queries the MediaWiki API of tolkiengateway.net to:
- list pages (via `allpages`),
- retrieve the wikitext of each page (`parse`),
- extract the infobox (block {{Infobox ... }} with handling of nested braces),
- save each infobox in the `infoboxes/` folder with a Windows-safe filename,
- log status to `infoboxes/infobox_log.txt`.

Main Functions
- `safe_filename_from_title(title, max_length=180)`: normalizes titles into Windows-safe filenames (replaces forbidden characters, handles reserved names, truncates).
- `get_infobox_wikitext(page_title)`: fetches raw wikitext of a page via `action=parse`.
- `extract_infobox(wikitext)`: isolates the infobox by counting `{{` / `}}` to handle nesting.
- `get_all_page_titles(limit=500)`: paginates through `list=allpages` to collect titles (script uses `limit=50` by default).
- `get_all_infobox_template_titles(limit=500)`: (optional) lists infobox templates via the `Infobox_templates` category.

Input/Output
- Input: no user input (limit parameter hard-coded, modifiable).
- Output: `infobox_*.txt` files in `infoboxes/` + `infobox_log.txt` (OK / NO INFOBOX / NO WIKITEXT).

Requirements
- Python 3.8+ and the `requests` package.
- Install dependencies: `pip install -r requirements.txt` (or `pip install requests`).

Usage
- Run: `python ApiRequestWithFastApi/requestAllInfobox.py`
- Adjust `limit` as needed (larger = more pages = slower).
- Site courtesy: the script uses a `User-Agent` and processes sequentially; add `time.sleep()` if you significantly increase `limit`.

Notes
- Filenames are cleaned to avoid Windows errors (forbidden characters, reserved names like CON/PRN, trailing spaces/dots).
- Infobox extraction accounts for nested braces; if no infobox is found, the log notes `NO INFOBOX`.
- On HTTP error, the script prints the code and a response excerpt.
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
    Extracts the content of a wikitext section (e.g., ==Other names==).
    Returns None if the section is not found.
    """
    pattern = rf"^==\s*{re.escape(section_title)}\s*==\s*(.*?)(?=^==[^=]|\Z)"
    match = re.search(pattern, wikitext, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def get_existing_titles_from_infoboxes(output_dir="infoboxes"):
    """
    Extracts the titles of pages already downloaded.
    Extracts the title from the first line: --- Page Title ---
    Useful for incremental mode.
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
    Retrieves pages from a specific category.
    Very effective for targeting a type of content (e.g., characters).
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
    Fetches pages that use infobox templates.
    More efficient than fetching all pages.
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
    print("MODE 1: Fetching pages from Characters category...")
    all_titles = get_pages_from_category("Category:Characters", limit=500)
elif MODE == 2:
    print("MODE 2: Fetching pages with infobox templates...")
    all_titles = get_pages_with_infobox(limit=500)
else:
    print("MODE 3: Fetching all pages (not recommended)...")
    all_titles = get_all_page_titles(limit=50)

if INCREMENTAL:
    existing_titles = get_existing_titles_from_infoboxes(output_dir)
    initial_count = len(all_titles)
    all_titles = [t for t in all_titles if t not in existing_titles]
    skipped_count = initial_count - len(all_titles)
    print(f"Incremental mode enabled:")
    print(f"  • Pages to process initially:  {initial_count}")
    print(f"  • Pages already downloaded:    {skipped_count}")
    print(f"  • Pages to download:           {len(all_titles)}")
else:
    print("Incremental mode disabled: all pages will be processed")

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
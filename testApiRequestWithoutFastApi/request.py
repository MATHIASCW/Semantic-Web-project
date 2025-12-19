import json
import os
import re
import requests

API = "https://tolkiengateway.net/w/api.php"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
}
TIMEOUT_SEC = 15

def get_infobox_wikitext(page_title):
    print(f"Request parse: {page_title}", flush=True)
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json"
    }
    try:
        resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
    except requests.RequestException as exc:
        print(f"HTTP error (parse): {exc}", flush=True)
        return None
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
    match = re.search(r"\{\{\s*infobox\b", wikitext, flags=re.IGNORECASE)
    if not match:
        print("No infobox found.")
        return None
    start = match.start()
    count = 0
    i = start
    while i < len(wikitext) - 1:
        if wikitext[i:i+2] == '{{':
            count += 1
            i += 2
            continue
        if wikitext[i:i+2] == '}}':
            count -= 1
            i += 2
            if count == 0:
                return wikitext[start:i]
            continue
        i += 1
    print("No complete infobox found.")
    return None


# Get all page titles from the wiki
def get_all_page_titles(limit=100):
    print(f"Request allpages: max_titles={limit}", flush=True)
    params = {
        "action": "query",
        "list": "allpages",
        "format": "json",
        "aplimit": min(limit, 500),
    }
    titles = []
    cont = {}
    while len(titles) < limit:
        params.update(cont)
        try:
            resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
        except requests.RequestException as exc:
            print(f"HTTP error (allpages): {exc}", flush=True)
            break
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        data = resp.json()
        if "query" not in data or "allpages" not in data["query"]:
            print("Unexpected response structure:", data, flush=True)
            break
        for p in data["query"]["allpages"]:
            titles.append(p["title"])
            if len(titles) >= limit:
                break
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    print(f"Collected {len(titles)} page titles", flush=True)
    return titles

def get_all_page_titles_page(limit=500, cont=None):
    params = {
        "action": "query",
        "list": "allpages",
        "format": "json",
        "aplimit": limit,
    }
    if cont:
        params.update(cont)
    try:
        resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
    except requests.RequestException as exc:
        print(f"HTTP error (allpages page): {exc}", flush=True)
        return [], None
    if resp.status_code != 200:
        print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
        return [], None
    data = resp.json()
    if "query" not in data or "allpages" not in data["query"]:
        print("Unexpected response structure:", data, flush=True)
        return [], None
    titles = [p["title"] for p in data["query"]["allpages"]]
    next_cont = data.get("continue")
    return titles, next_cont

def get_titles_with_infobox(limit=100):
    print(f"Request search: infobox max_titles={limit}", flush=True)
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srsearch": "insource:{{Infobox",
        "srnamespace": 0,
        "srlimit": min(limit, 50),
    }
    titles = []
    cont = {}
    while len(titles) < limit:
        params.update(cont)
        try:
            resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
        except requests.RequestException as exc:
            print(f"HTTP error (search): {exc}", flush=True)
            break
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        data = resp.json()
        if "query" not in data or "search" not in data["query"]:
            print("Unexpected response structure:", data, flush=True)
            break
        for item in data["query"]["search"]:
            titles.append(item["title"])
            if len(titles) >= limit:
                break
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    print(f"Collected {len(titles)} infobox titles", flush=True)
    return titles

def get_pages_using_template(template_title, limit=100):
    print(f"Request embeddedin: {template_title} max_titles={limit}", flush=True)
    params = {
        "action": "query",
        "list": "embeddedin",
        "eititle": template_title,
        "eilimit": min(limit, 500),
        "format": "json",
    }
    titles = []
    cont = {}
    while len(titles) < limit:
        params.update(cont)
        try:
            resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
        except requests.RequestException as exc:
            print(f"HTTP error (embeddedin): {exc}", flush=True)
            break
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        data = resp.json()
        if "query" not in data or "embeddedin" not in data["query"]:
            print("Unexpected response structure:", data, flush=True)
            break
        for item in data["query"]["embeddedin"]:
            titles.append(item["title"])
            if len(titles) >= limit:
                break
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    print(f"Collected {len(titles)} titles for {template_title}", flush=True)
    return titles

def get_infobox_templates_from_category(category_title, limit=500):
    print(f"Request categorymembers: {category_title}", flush=True)
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_title,
        "cmnamespace": 10,
        "cmlimit": min(limit, 500),
        "format": "json",
    }
    titles = []
    cont = {}
    while len(titles) < limit:
        params.update(cont)
        try:
            resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
        except requests.RequestException as exc:
            print(f"HTTP error (categorymembers): {exc}", flush=True)
            break
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        data = resp.json()
        if "query" not in data or "categorymembers" not in data["query"]:
            print("Unexpected response structure:", data, flush=True)
            break
        for item in data["query"]["categorymembers"]:
            titles.append(item["title"])
            if len(titles) >= limit:
                break
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    print(f"Collected {len(titles)} templates from {category_title}", flush=True)
    return titles

def load_templates_cache(cache_path):
    if not os.path.exists(cache_path):
        return []
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cache read error: {exc}", flush=True)
        return []
    if not isinstance(data, list):
        return []
    return [str(x) for x in data if x]

def save_templates_cache(cache_path, templates):
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(templates, f, indent=2)
    except OSError as exc:
        print(f"Cache write error: {exc}", flush=True)

def get_infobox_templates_cached(category_title, cache_path, refresh=False):
    if not refresh:
        cached = load_templates_cache(cache_path)
        if cached:
            print(f"Loaded {len(cached)} templates from cache", flush=True)
            return cached
    templates = get_infobox_templates_from_category(category_title)
    if templates:
        save_templates_cache(cache_path, templates)
    return templates

def get_page_links(page_title, limit=200):
    params = {
        "action": "query",
        "prop": "links",
        "titles": page_title,
        "format": "json",
        "pllimit": min(limit, 500),
    }
    links = []
    cont = {}
    while len(links) < limit:
        params.update(cont)
        try:
            resp = requests.get(API, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SEC)
        except requests.RequestException as exc:
            print(f"HTTP error (links): {exc}", flush=True)
            break
        if resp.status_code != 200:
            print(f"HTTP error: {resp.status_code}\nResponse text: {resp.text[:500]}")
            break
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            for item in page.get("links", []):
                title = item.get("title")
                if not title:
                    continue
                if ":" in title:
                    continue
                links.append(title)
                if len(links) >= limit:
                    break
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    return links

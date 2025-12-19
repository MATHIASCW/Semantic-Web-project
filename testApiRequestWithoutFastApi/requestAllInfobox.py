import requests
import re
import time
import os

API = "https://tolkiengateway.net/w/api.php"

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
                filename = os.path.join(output_dir, f"infobox_{idx:03d}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"--- {title} ---\n{infobox}\n")
                print(f"Saved infobox for '{title}' to {filename}")
                log.write(f"OK: {idx}: {title}\n")
            else:
                print(f"No infobox found for '{title}'")
                log.write(f"NO INFOBOX: {idx}: {title}\n")
        else:
            print(f"No wikitext found for '{title}'")
            log.write(f"NO WIKITEXT: {idx}: {title}\n")
end_time = time.time()
print(f"Finished processing {len(all_titles)} pages in {end_time - start_time:.2f} seconds.")
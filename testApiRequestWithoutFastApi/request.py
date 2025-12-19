import requests
import re

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
        print("No infobox found.")
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


# Get all page titles from the wiki
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

# Fetch and print infobox for each page
all_titles = get_all_page_titles(limit=50)  # You can increase the limit, but start small for testing
for title in all_titles:
    wikitext = get_infobox_wikitext(title)
    if wikitext:
        infobox = extract_infobox(wikitext)
        if infobox:
            print(f"--- {title} ---\n{infobox}\n")
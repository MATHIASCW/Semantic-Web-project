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

wikitext = get_infobox_wikitext("Elrond")
infobox = extract_infobox(wikitext)
print(infobox)    


import requests
from infobox_parser import extract_infobox, parse_infobox_fields

API_URL = "https://tolkiengateway.net/w/api.php"

def get_wikitext(page_title: str) -> str:
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json"
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    data = response.json()
    return data["parse"]["wikitext"]["*"]


if __name__ == "__main__":
    text = get_wikitext("Elrond")
    infobox = extract_infobox(text)

    fields = parse_infobox_fields(infobox)
    for k, v in fields.items():
        print(k, "=>", v)

    # print(infobox)


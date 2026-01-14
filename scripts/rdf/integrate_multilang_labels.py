import time
import requests
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDFS, RDF

API_URL = "https://lotr.fandom.com/api.php"
USER_AGENT = "TolkienKGBot/1.0 (student project; contact: you@example.com)"
REQUEST_DELAY_SEC = 0.4
BATCH_SIZE = 50

INPUT_TTL = "data/rdf/all_infoboxes.ttl"
OUTPUT_TTL = "data/rdf/multilang_labels.ttl"

SCHEMA = Namespace("http://schema.org/")


def normalize_label(value: str) -> str:
    text = (value or "").strip().lower()
    text = text.replace("_", " ")
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
    text = "".join(cleaned)
    return " ".join(text.split())


def build_label_index(graph: Graph):
    label_to_uris = {}
    for s, p, o in graph.triples((None, None, None)):
        if p not in (SCHEMA.name, RDFS.label):
            continue
        if not isinstance(o, Literal):
            continue
        key = normalize_label(str(o))
        if not key:
            continue
        label_to_uris.setdefault(key, set()).add(s)
    return label_to_uris


def fetch_langlinks(titles):
    params = {
        "action": "query",
        "prop": "langlinks",
        "lllimit": "max",
        "format": "json",
        "redirects": 1,
        "titles": "|".join(titles),
    }
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(API_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    kg = Graph()
    kg.parse(INPUT_TTL, format="turtle")

    label_to_uris = build_label_index(kg)
    label_to_uri = {}
    for key, uris in label_to_uris.items():
        if len(uris) == 1:
            label_to_uri[key] = next(iter(uris))

    titles = list(label_to_uri.keys())

    out = Graph()
    out.bind("rdfs", RDFS)

    total_pages = 0
    total_labels = 0
    languages = set()

    for i in range(0, len(titles), BATCH_SIZE):
        batch = titles[i : i + BATCH_SIZE]
        try:
            data = fetch_langlinks(batch)
        except Exception:
            continue

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            title = page.get("title")
            if not title:
                continue
            key = normalize_label(title)
            uri = label_to_uri.get(key)
            if not uri:
                continue

            total_pages += 1
            for link in page.get("langlinks", []):
                lang = link.get("lang")
                value = link.get("*")
                if not lang or not value:
                    continue
                languages.add(lang)
                out.add((uri, RDFS.label, Literal(value, lang=lang)))
                total_labels += 1

        time.sleep(REQUEST_DELAY_SEC)

    out.serialize(destination=OUTPUT_TTL, format="turtle")
    print(f"OK. Labels written: {OUTPUT_TTL}")
    print(f"  - Entities matched: {total_pages}")
    print(f"  - Labels added: {total_labels}")
    print(f"  - Languages: {', '.join(sorted(languages))}")


if __name__ == "__main__":
    main()



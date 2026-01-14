import csv
import json
from pathlib import Path
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef

KGRES = Namespace("http://tolkien-kg.org/resource/")
KGONT = Namespace("http://tolkien-kg.org/ontology/")
SCHEMA = Namespace("http://schema.org/")
KGCARD = Namespace("http://tolkien-kg.org/card/")

INPUT_TTL = Path("data/rdf/all_infoboxes.ttl")
CARDS_JSON = Path("data/rdf/cards.json")
CSV_CHARACTERS = Path("data/rdf/lotr_characters.csv")
OUTPUT_TTL = Path("data/rdf/external_links.ttl")

ADD_DBPEDIA_SAMEAS = True


def normalize_name(value: str) -> str:
    text = (value or "").strip().lower()
    text = text.replace("_", " ")
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
    text = "".join(cleaned)
    return " ".join(text.split())


def build_label_index(graph: Graph) -> dict:
    labels = {}
    for s, p, o in graph.triples((None, None, None)):
        if p not in (SCHEMA.name, RDFS.label):
            continue
        if not isinstance(o, Literal):
            continue
        key = normalize_name(str(o))
        if not key:
            continue
        labels.setdefault(key, set()).add(s)
    return labels


def find_entity(labels_index: dict, name: str):
    key = normalize_name(name)
    if not key:
        return None
    uris = labels_index.get(key)
    if not uris:
        return None
    return next(iter(uris))


def dbpedia_uri(name: str) -> URIRef:
    safe = quote(name.replace(" ", "_"))
    return URIRef(f"http://dbpedia.org/resource/{safe}")


def add_dbpedia_link(graph: Graph, entity_uri: URIRef, name: str, linked: set):
    if not ADD_DBPEDIA_SAMEAS:
        return
    if entity_uri in linked:
        return
    graph.add((entity_uri, OWL.sameAs, dbpedia_uri(name)))
    linked.add(entity_uri)


def integrate_cards(graph: Graph, labels_index: dict, linked_dbpedia: set) -> int:
    if not CARDS_JSON.exists():
        return 0
    count = 0
    with CARDS_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for _set_id, set_data in data.items():
        base_urls = set_data.get("imageBaseUrl", {})
        cards = set_data.get("cards", {})
        for card_id, card in cards.items():
            name_by_lang = card.get("name", {})
            if not isinstance(name_by_lang, dict):
                continue

            entity_uri = None
            matched_name = None
            for lang, label in name_by_lang.items():
                if not label:
                    continue
                entity_uri = find_entity(labels_index, label)
                if entity_uri:
                    matched_name = label
                    break

            if not entity_uri:
                continue

            card_uri = KGCARD[card_id]
            graph.add((card_uri, RDF.type, SCHEMA.CreativeWork))
            graph.add((card_uri, SCHEMA.identifier, Literal(card_id)))
            graph.add((entity_uri, SCHEMA.subjectOf, card_uri))
            graph.add((card_uri, SCHEMA.about, entity_uri))

            image_file = card.get("image")
            if image_file:
                base_url = base_urls.get("en") or next(iter(base_urls.values()), "")
                if base_url:
                    graph.add((card_uri, SCHEMA.image, URIRef(f"{base_url}{image_file}")))

            for lang, label in name_by_lang.items():
                if not label:
                    continue
                lang_tag = lang if lang.isalpha() else None
                graph.add((card_uri, RDFS.label, Literal(label, lang=lang_tag)))
                graph.add((entity_uri, RDFS.label, Literal(label, lang=lang_tag)))

            if matched_name:
                add_dbpedia_link(graph, entity_uri, matched_name, linked_dbpedia)
            count += 1
    return count


def integrate_csv(graph: Graph, labels_index: dict, linked_dbpedia: set) -> int:
    if not CSV_CHARACTERS.exists():
        return 0
    count = 0
    with CSV_CHARACTERS.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            entity_uri = find_entity(labels_index, name)
            if not entity_uri:
                continue

            graph.add((entity_uri, RDFS.label, Literal(name, lang="en")))
            add_dbpedia_link(graph, entity_uri, name, linked_dbpedia)

            field_map = {
                "birth": KGONT.birthDate,
                "death": KGONT.deathDate,
                "gender": SCHEMA.gender,
                "hair": KGONT.hair,
                "height": KGONT.height,
                "race": KGONT.race,
                "realm": KGONT.realm,
                "spouse": KGONT.spouse,
            }
            for key, pred in field_map.items():
                value = (row.get(key) or "").strip()
                if value:
                    graph.add((entity_uri, pred, Literal(value)))

            count += 1
    return count


def main():
    if not INPUT_TTL.exists():
        raise FileNotFoundError(f"Missing input: {INPUT_TTL}")

    kg = Graph()
    kg.parse(INPUT_TTL, format="turtle")

    out = Graph()
    out.bind("kg-res", KGRES)
    out.bind("kg-ont", KGONT)
    out.bind("schema", SCHEMA)
    out.bind("rdfs", RDFS)
    out.bind("owl", OWL)
    out.bind("kg-card", KGCARD)

    labels_index = build_label_index(kg)
    linked_dbpedia = set()

    cards_count = integrate_cards(out, labels_index, linked_dbpedia)
    csv_count = integrate_csv(out, labels_index, linked_dbpedia)

    out.serialize(destination=str(OUTPUT_TTL), format="turtle")
    try:
        with open(OUTPUT_TTL, "r", encoding="utf-8") as f:
            content = f.read()
        if "@prefix schema1:" in content:
            content = content.replace("@prefix schema1:", "@prefix schema:")
            content = content.replace("schema1:", "schema:")
            with open(OUTPUT_TTL, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception:
        pass
    print(f"OK. External triples written: {OUTPUT_TTL}")
    print(f"  - Cards linked: {cards_count}")
    print(f"  - CSV rows linked: {csv_count}")
    print(f"  - DBpedia links added: {len(linked_dbpedia)}")


if __name__ == "__main__":
    main()



from rdflib import Graph

INPUTS = [
    "data/rdf/all_infoboxes_with_lang.ttl",
    "data/rdf/external_links.ttl",
]
OUTPUT = "data/rdf/kg_full.ttl"


def main():
    merged = Graph()
    for path in INPUTS:
        merged.parse(path, format="turtle")
    merged.serialize(destination=OUTPUT, format="turtle")
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            content = f.read()
        if "@prefix schema1:" in content:
            content = content.replace("@prefix schema1:", "@prefix schema:")
            content = content.replace("schema1:", "schema:")
            with open(OUTPUT, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception:
        pass
    print(f"OK. Merged TTL written: {OUTPUT}")


if __name__ == "__main__":
    main()



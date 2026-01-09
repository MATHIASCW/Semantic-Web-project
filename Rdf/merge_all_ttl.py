from rdflib import Graph

INPUTS = [
    "RdfData/all_infoboxes_with_lang.ttl",
    "RdfData/external_links.ttl",
]
OUTPUT = "RdfData/kg_full.ttl"


def main():
    merged = Graph()
    for path in INPUTS:
        merged.parse(path, format="turtle")
    merged.serialize(destination=OUTPUT, format="turtle")
    print(f"OK. Merged TTL written: {OUTPUT}")


if __name__ == "__main__":
    main()

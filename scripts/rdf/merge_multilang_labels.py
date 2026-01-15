"""
Merge multilingual labels into the Tolkien KG and ensure English fallbacks.
Combines base infobox triples with fetched langlink labels, adds missing
`rdfs:label@en` using schema:name or existing untagged labels, and writes
data/rdf/all_infoboxes_with_lang.ttl for downstream merging.
"""

from rdflib import Graph, Literal
from rdflib.namespace import RDFS
from rdflib import Namespace

SCHEMA = Namespace("http://schema.org/")

INPUT_TTL = "data/rdf/all_infoboxes.ttl"
LABELS_TTL = "data/rdf/multilang_labels.ttl"
OUTPUT_TTL = "data/rdf/all_infoboxes_with_lang.ttl"


def has_en_label(graph: Graph, subject) -> bool:
    for _, _, o in graph.triples((subject, RDFS.label, None)):
        if isinstance(o, Literal) and o.language == "en":
            return True
    return False


def main():
    kg = Graph()
    kg.parse(INPUT_TTL, format="turtle")

    labels = Graph()
    labels.parse(LABELS_TTL, format="turtle")

    for triple in labels:
        kg.add(triple)

    en_labels = {s for s, _, o in kg.triples((None, RDFS.label, None)) if isinstance(o, Literal) and o.language == "en"}

    for s, _, o in kg.triples((None, SCHEMA.name, None)):
        if not isinstance(o, Literal):
            continue
        if s in en_labels:
            continue
        kg.add((s, RDFS.label, Literal(str(o), lang="en")))
        en_labels.add(s)

    for s, _, o in kg.triples((None, RDFS.label, None)):
        if not isinstance(o, Literal) or o.language:
            continue
        if s in en_labels:
            continue
        kg.add((s, RDFS.label, Literal(str(o), lang="en")))
        en_labels.add(s)

    kg.serialize(destination=OUTPUT_TTL, format="turtle")
    print(f"OK. Merged KG written: {OUTPUT_TTL}")


if __name__ == "__main__":
    main()



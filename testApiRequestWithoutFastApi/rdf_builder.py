from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import html
import re
from urllib.parse import quote

BASE = "https://tolkien-kg.org/resource/"
PAGE_BASE = "https://tolkiengateway.net/wiki/"
KG = Namespace("https://tolkien-kg.org/ontology/")
SCHEMA = Namespace("https://schema.org/")

ENTITY_FIELDS = {
    "spouse": SCHEMA.spouse,
    "husband": SCHEMA.spouse,
    "wife": SCHEMA.spouse,
    "child": SCHEMA.child,
    "children": SCHEMA.children,
    "parent": SCHEMA.parent,
    "father": SCHEMA.father,
    "mother": SCHEMA.mother,
    "birthlocation": SCHEMA.birthPlace,
    "birthplace": SCHEMA.birthPlace,
    "deathlocation": SCHEMA.deathPlace,
    "deathplace": SCHEMA.deathPlace,
    "birth_place": SCHEMA.birthPlace,
    "death_place": SCHEMA.deathPlace,
    "location": SCHEMA.location,
    "realm": SCHEMA.location,
    "affiliation": SCHEMA.affiliation,
    "allegiance": SCHEMA.affiliation,
    "occupation": SCHEMA.occupationalCategory,
    "race": SCHEMA.species,
    "species": SCHEMA.species,
    "house": SCHEMA.memberOf,
    "family": SCHEMA.memberOf,
    "people": SCHEMA.memberOf,
}

LITERAL_FIELDS = {
    "birth_date": (SCHEMA.birthDate, XSD.date),
    "death_date": (SCHEMA.deathDate, XSD.date),
    "years": (SCHEMA.temporal, None),
    "gender": (SCHEMA.gender, None),
}

LITERAL_ONLY_FIELDS = {
    "age",
    "birth",
    "death",
    "caption",
    "image",
    "name",
    "othernames",
    "position",
    "pronun",
    "rule",
}

LINK_RE = re.compile(r"\[\[([^|\]]+)(?:\|[^\]]+)?\]\]")
LINK_MARKUP_RE = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.DOTALL)
TEMPLATE_RE = re.compile(r"\{\{[^{}]*\}\}")
HTML_TAG_RE = re.compile(r"<[^>]+>")
ITALIC_RE = re.compile(r"''+")

def normalize_label(label: str) -> str:
    label = re.sub(r"\s+", " ", label.strip())
    label = label.replace(" ", "_")
    return label

def make_uri(label: str) -> URIRef:
    safe = quote(normalize_label(label), safe="_-~()'")
    return URIRef(BASE + safe)

def make_page_uri(label: str) -> URIRef:
    safe = quote(normalize_label(label), safe="_-~()'")
    return URIRef(PAGE_BASE + safe)

def parse_infobox_fields(infobox: str) -> dict:
    fields = {}
    for line in infobox.splitlines():
        if line.startswith("|") and "=" in line:
            k, v = line[1:].split("=", 1)
            fields[k.strip().lower()] = v.strip()
    return fields

def sanitize_literal(value: str) -> str:
    value = value.replace('"', "'")
    value = re.sub(r"\s+", " ", value).strip()
    return value

def is_empty_value(value: str) -> bool:
    v = value.strip().lower()
    return v in {"", "-", "—", "none", "unknown", "n/a", "na", "?"}

def cleanup_value(value: str) -> str:
    value = REF_RE.sub("", value)
    value = TEMPLATE_RE.sub("", value)
    value = HTML_TAG_RE.sub("", value)
    value = ITALIC_RE.sub("", value)
    value = LINK_MARKUP_RE.sub(lambda m: (m.group(2) or m.group(1) or ""), value)
    value = html.unescape(value)
    return value.strip()

def extract_link_targets(value: str):
    targets = []
    for m in LINK_RE.finditer(value):
        target = m.group(1).strip()
        if ":" in target:
            continue
        targets.append(target)
    return targets

def split_entities(value: str):
    parts = re.split(r"<br\s*/?>|,|;|/", value)
    return [p.strip() for p in parts if p.strip()]

def infer_predicate(field: str) -> URIRef:
    return ENTITY_FIELDS.get(field, KG[re.sub(r"[^a-z0-9_]", "_", field)])

def looks_like_entity(value: str) -> bool:
    if is_empty_value(value):
        return False
    if re.fullmatch(r"[\d\W_]+", value):
        return False
    return any(c.isupper() for c in value)

def infobox_to_rdf(title: str, infobox: str) -> Graph:
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("kg", KG)

    s = make_uri(title)
    g.add((s, RDF.type, SCHEMA.Thing))
    g.add((s, RDFS.label, Literal(title)))

    fields = parse_infobox_fields(infobox)

    for field, raw_value in fields.items():
        if not raw_value:
            continue

        value = cleanup_value(raw_value)
        if not value or is_empty_value(value):
            continue

        if field in LITERAL_FIELDS:
            pred, datatype = LITERAL_FIELDS[field]
            if datatype:
                g.add((s, pred, Literal(sanitize_literal(value), datatype=datatype)))
            else:
                g.add((s, pred, Literal(sanitize_literal(value))))
            continue

        pred = infer_predicate(field)
        if field in LITERAL_ONLY_FIELDS:
            g.add((s, pred, Literal(sanitize_literal(value))))
            continue

        link_targets = extract_link_targets(value)
        if link_targets:
            for ent in link_targets:
                g.add((s, pred, make_uri(ent)))
            continue

        if field in ENTITY_FIELDS:
            for ent in split_entities(value):
                if is_empty_value(ent):
                    continue
                if looks_like_entity(ent):
                    g.add((s, pred, make_uri(ent)))
                else:
                    g.add((s, pred, Literal(sanitize_literal(ent))))
        else:
            g.add((s, pred, Literal(sanitize_literal(value))))

    return g

def base_entity_graph(title: str) -> Graph:
    g = Graph()
    g.bind("schema", SCHEMA)
    s = make_uri(title)
    page = make_page_uri(title)
    g.add((s, RDF.type, SCHEMA.Thing))
    g.add((s, RDFS.label, Literal(title)))
    g.add((s, SCHEMA.mainEntityOfPage, page))
    g.add((page, RDF.type, SCHEMA.WebPage))
    g.add((page, SCHEMA.about, s))
    return g

def add_links_to_graph(g: Graph, title: str, links) -> None:
    s = make_uri(title)
    for link in links:
        g.add((s, SCHEMA.mentions, make_uri(link)))

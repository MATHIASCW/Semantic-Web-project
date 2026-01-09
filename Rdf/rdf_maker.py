import os
import re
import unicodedata
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD, RDFS
import wikitextparser as wtp

INPUT_DIR = "infoboxes"
OUTPUT_DIR = "RdfData"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "all_infoboxes.ttl")

KGONT = Namespace("http://tolkien-kg.org/ontology/")
KGRES = Namespace("http://tolkien-kg.org/resource/")
SCHEMA = Namespace("http://schema.org/")


def _normalize_template_key(template_name: str) -> str:
    n = (template_name or "").strip().lower()
    n = re.sub(r"^infobox\s+", "", n)
    n = re.sub(r"\s+infobox$", "", n)
    n = re.sub(r"\s+", " ", n)
    return n


def _extract_infobox_block(wikitext: str) -> str | None:
    """Return the raw {{Infobox ...}} block if found (balanced braces)."""
    start = wikitext.lower().find("{{infobox")
    if start == -1:
        return None
    count = 0
    for i in range(start, len(wikitext)):
        if wikitext[i : i + 2] == "{{":
            count += 1
        elif wikitext[i : i + 2] == "}}":
            count -= 1
            if count == 0:
                return wikitext[start : i + 2]
    return None


def clean_value(value: str, preserve_timeline: bool = False) -> str:
    v = value or ""
    v = re.sub(r"<ref[^>]*>.*?</ref>", "", v, flags=re.DOTALL | re.IGNORECASE)
    v = re.sub(r"<ref[^/>]*/>", "", v, flags=re.IGNORECASE)
    v = re.sub(r"</?ref[^>]*>", "", v, flags=re.IGNORECASE)

    external_link_match = re.search(r"\[(https?://[^\s\]]+)", v)
    if external_link_match:
        v = external_link_match.group(1)

    v = re.sub(r"<br\s*/?>", "|||", v, flags=re.IGNORECASE)
    v = re.sub(r"</?nowiki[^>]*>", "", v, flags=re.IGNORECASE)
    v = re.sub(r"</?(small|span|sup|sub|i|b|div|p|strong|em)[^>]*>", "", v, flags=re.IGNORECASE)
    v = re.sub(r"<[^>]+>", "", v)

    v = v.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    v = v.replace("&lt;", "<").replace("&gt;", ">")

    if not preserve_timeline:
        timeline_match = re.search(r"\{\{Timeline\s*\|(.*?)\}\}", v, flags=re.DOTALL | re.IGNORECASE)
        if timeline_match:
            pass

    v = re.sub(r"\{\{SR\|(\d+)\}\}", r"SR \1", v)
    v = re.sub(r"\{\{TA\|(\d+)(\|[^}]+)?\}\}", r"TA \1", v)
    v = re.sub(r"\{\{FA\|(\d+)(\|[^}]+)?\}\}", r"FA \1", v)
    v = re.sub(r"\{\{SA\|(\d+)(\|[^}]+)?\}\}", r"SA \1", v)
    v = re.sub(r"\{\{YT\|(\d+)(\|[^}]+)?\}\}", r"YT \1", v)
    v = re.sub(r"\{\{FoA\|(\d+)(\|[^}]+)?\}\}", r"FoA \1", v)

    if preserve_timeline:
        v = re.sub(r"\{\{(?!Timeline)([^}]+)\}\}", "", v, flags=re.IGNORECASE)
    else:
        v = re.sub(r"\{\{[^}]+\}\}", "", v)

    v = re.sub(r"\{\{(IPA|fact|citation needed|cn)[^}]*\}\}", "", v, flags=re.IGNORECASE)

    v = re.sub(r"'{2,}", "", v)

    if preserve_timeline and "{{Timeline" in v:
        return v.strip()

    v = re.sub(r"\s+", " ", v)
    return v.strip()


LINK_RE = re.compile(r"\[\[(.+?)(\|(.+?))?\]\]")
SEPARATORS = re.compile(r"\s*[,;/]\s*|\s+and\s+|\n+|\r\n+", re.IGNORECASE)

LITERAL_ONLY_PROPS = {
    KGONT.birthDate,
    KGONT.deathDate,
    KGONT.height,
    KGONT.weapons,
    KGONT.steed,
    KGONT.age,
    SCHEMA.age,
    SCHEMA.gender,
    KGONT.clothing,
    KGONT.timeline,
    KGONT.rule,
    KGONT.rulePeriod,
    KGONT.rulePeriod,
    KGONT.hair,
    KGONT.eyes,
    KGONT.chronology,
}

PROPERTY_MAP = {
    "name": SCHEMA.name,
    "fullname": SCHEMA.name,
    "full name": SCHEMA.name,
    "othername": KGONT.other_names,
    "other name": KGONT.other_names,
    "other names": KGONT.other_names,
    "othernames": KGONT.other_names,
    "also_known_as": KGONT.other_names,
    "aka": KGONT.other_names,
    "nickname": KGONT.other_names,
    "birth": KGONT.birthDate,
    "birthdate": KGONT.birthDate,
    "born": KGONT.birthDate,
    "death": KGONT.deathDate,
    "deathdate": KGONT.deathDate,
    "died": KGONT.deathDate,
    "birthlocation": KGONT.birthLocation,
    "birth location": KGONT.birthLocation,
    "brithlocation": KGONT.birthLocation,
    "deathlocation": KGONT.deathLocation,
    "death location": KGONT.deathLocation,
    "location": SCHEMA.location,
    "birthplace": SCHEMA.birthPlace,
    "deathplace": SCHEMA.deathPlace,
    "parentage": KGONT.parentage,
    "parents": KGONT.parentage,
    "father": KGONT.parentage,
    "mother": KGONT.parentage,
    "children": KGONT.children,
    "child": KGONT.children,
    "spouse": KGONT.spouse,
    "partner": KGONT.spouse,
    "house": KGONT.family,
    "family": KGONT.family,
    "gender": SCHEMA.gender,
    "race": KGONT.race,
    "titles": KGONT.position,
    "title": KGONT.position,
    "occupation": KGONT.occupation,
    "position": KGONT.position,
    "age": SCHEMA.age,
    "height": KGONT.height,
    "weapons": KGONT.weapons,
    "weapon": KGONT.weapons,
    "steed": KGONT.steed,
    "mount": KGONT.steed,
    "horse": KGONT.steed,
    "clothing": KGONT.clothing,
    "clothes": KGONT.clothing,
    "hair": KGONT.hair,
    "eyes": KGONT.eyes,
    "eyecolor": KGONT.eyeColor,
    "eye_color": KGONT.eyeColor,
    "haircolor": KGONT.hairColor,
    "hair_color": KGONT.hairColor,
    "rule": KGONT.rule,
    "rulePeriod": KGONT.rulePeriod,
    "ruleperiod": KGONT.rulePeriod,
    "image": SCHEMA.image,
    "caption": SCHEMA.caption,
    "people": KGONT.people,
    "pronun": KGONT.pronunciation,
    "pronunciation": KGONT.pronunciation,
    "notablefor": SCHEMA.description,
    "notable for": SCHEMA.description,
    "description": SCHEMA.description,
    "timeline": KGONT.timeline,
    "chronology": KGONT.timeline,
    "affiliation": KGONT.affiliation,
    "siblings": KGONT.sibling,
    "sibling": KGONT.sibling,
    "website": SCHEMA.url,
    "education": SCHEMA.educationalCredentialAwarded,
    "educated": SCHEMA.educationalCredentialAwarded,
    "language": SCHEMA.inLanguage,
    "languages": SCHEMA.inLanguage,
    "hair color": KGONT.hairColor,
    "eye color": KGONT.eyeColor,
    "skin": KGONT.skinColor,
    "skin colour": KGONT.skinColor,
    "color": KGONT.color,
    "colour": KGONT.color,
    "affiliation": KGONT.affiliation,
    "realm": KGONT.realm,
    "created": KGONT.created,
    "destroyed": KGONT.destroyed,
    "owner": KGONT.owner,
    "creator": KGONT.creator,
    "publisher": SCHEMA.publisher,
    "author": SCHEMA.author,
    "released": SCHEMA.datePublished,
    "releasedate": SCHEMA.datePublished,
    "published": SCHEMA.datePublished,
    "director": SCHEMA.director,
    "genre": SCHEMA.genre,
    "platform": SCHEMA.applicationCategory,
    "developer": SCHEMA.developer,
    "founded": SCHEMA.foundingDate,
    "founder": SCHEMA.founder,
    "type": SCHEMA.additionalType,
    "inhabitants": KGONT.inhabitants,
    "events": KGONT.events,
    "regions": KGONT.regions,
    "settlements": KGONT.settlements,
    "purpose": KGONT.purpose,
    "members": KGONT.members,
    "origin": KGONT.origin,
    "lifespan": KGONT.lifespan,
    "heritage": KGONT.heritage,
    "hoard": KGONT.hoard,
    "slayer": KGONT.slayer,
    "ruler": KGONT.ruler,
}

TYPE_MAP = {
    "character": KGONT.Character,
    "characters": KGONT.Character,
    "person": SCHEMA.Person,
    "people": SCHEMA.Person,
    "author": SCHEMA.Person,
    "artist": SCHEMA.Person,
    "modernpeople": SCHEMA.Person,
    "scholar": SCHEMA.Person,
    "location": KGONT.Location,
    "place": KGONT.Location,
    "settlement": KGONT.Location,
    "city": KGONT.Location,
    "region": KGONT.Location,
    "river": KGONT.Location,
    "mountain": KGONT.Location,
    "film": SCHEMA.Movie,
    "movie": SCHEMA.Movie,
    "episode": SCHEMA.TVEpisode,
    "tv": SCHEMA.TVSeries,
    "tvseries": SCHEMA.TVSeries,
    "series": SCHEMA.TVSeries,
    "book": SCHEMA.Book,
    "novel": SCHEMA.Book,
    "poem": SCHEMA.CreativeWork,
    "letter": SCHEMA.CreativeWork,
    "album": SCHEMA.MusicAlbum,
    "song": SCHEMA.MusicRecording,
    "single": SCHEMA.MusicRecording,
    "video game": SCHEMA.VideoGame,
    "videogame": SCHEMA.VideoGame,
    "board game": SCHEMA.Game,
    "puzzle": SCHEMA.Game,
    "organization": SCHEMA.Organization,
    "company": SCHEMA.Organization,
    "group": SCHEMA.Organization,
    "noble house": KGONT.House,
    "house": KGONT.House,
    "object": KGONT.Object,
    "artifact": KGONT.Object,
    "weapon": KGONT.Object,
    "race": KGONT.Race,
    "language": SCHEMA.Language,
    "battle": KGONT.Battle,
    "war": KGONT.Battle,
}


def normalize_key(key: str) -> str:
    k = key.strip().lower()
    k = k.replace("_", " ")
    k = re.sub(r"\s+", " ", k)
    return k


def sanitize_local(name: str) -> str:
    t = name.strip().replace(" ", "_")
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = "".join(c if c.isalnum() or c in ("_", ".") else "_" for c in t)
    t = re.sub(r"_{2,}", "_", t).strip("_")
    return t or "unknown"


def to_res_iri(title: str):
    return KGRES[sanitize_local(title)]


def choose_type(template_name: str, data: dict):
    key = _normalize_template_key(template_name)
    if key in TYPE_MAP:
        return TYPE_MAP[key]
    for k, t in TYPE_MAP.items():
        if k in key:
            return t
    if any(k in data for k in ("gender", "birth", "death", "race", "parentage", "children", "spouse")):
        if any(k in data for k in ("occupation", "born", "died", "education", "website")):
            return SCHEMA.Person
        return KGONT.Character
    if any(k in data for k in ("location", "map", "settlement", "regions", "towns", "inhabitants")):
        return KGONT.Location
    if any(k in data for k in ("film", "episode", "runtime", "director", "imdb_id")):
        return SCHEMA.CreativeWork
    if any(k in data for k in ("book", "isbn", "publisher", "published")):
        return SCHEMA.Book
    if any(k in data for k in ("platform", "genre", "video game", "releasedate")):
        return SCHEMA.VideoGame
    return SCHEMA.CreativeWork


def parse_infobox_text(text: str):
    text_cleaned = re.sub(r"<ref[^>]*?/>", "", text, flags=re.IGNORECASE)
    text_cleaned = re.sub(r"<ref[^>]*?>.*?</ref>", "", text_cleaned, flags=re.DOTALL | re.IGNORECASE)
    text_cleaned = re.sub(r"</?ref[^>]*?>", "", text_cleaned, flags=re.IGNORECASE)

    block = _extract_infobox_block(text_cleaned) or text_cleaned

    parsed = wtp.parse(block)
    chosen_tpl = None
    for tpl in parsed.templates:
        name = (tpl.name or "").strip()
        if name.lower().startswith("infobox"):
            chosen_tpl = tpl
            break
        if chosen_tpl is None:
            chosen_tpl = tpl

    if not chosen_tpl:
        return "", {}

    name = chosen_tpl.name.strip()
    args = {}
    for arg in chosen_tpl.arguments:
        args[arg.name.strip()] = arg.value.strip()
    return name, args


def extract_other_names_section(full_text: str):
    """Extract other_names from embedded section after infobox."""
    lines = full_text.split("\n")
    in_section = False
    other_names = []
    for line in lines:
        if "--- Other names" in line or "--- Other Names" in line:
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("---") and "Other" not in line:
                break
            match = re.match(r"\*\s*'{0,3}\[?\[?([^]']+?)\]?\]?'{0,3}\s*[-:]", line)
            if match:
                name = match.group(1).strip()
                other_names.append(name)
    return other_names


def split_multi(raw: str, preserve_timeline: bool = False):
    cleaned = clean_value(raw, preserve_timeline=preserve_timeline)
    if preserve_timeline and "{{Timeline" in cleaned:
        return [cleaned]
    parts = cleaned.split("|||")
    result = []
    for part in parts:
        sub_parts = SEPARATORS.split(part)
        result.extend([p.strip() for p in sub_parts if p and p.strip() and len(p.strip()) > 1])
    return result if result else [cleaned.strip()]


def emit_literal(graph: Graph, subj, pred, text: str, preserve_timeline: bool = False):
    val = clean_value(text, preserve_timeline=preserve_timeline)
    if val:
        graph.add((subj, pred, Literal(val, datatype=XSD.string)))
        return True
    return False


def emit_links(graph: Graph, subj, pred, text: str, resource_labels: dict):
    """Emit IRIs and track resource labels for later materialization."""
    wrote = False
    for m in LINK_RE.finditer(text):
        target = m.group(1).strip()
        iri = to_res_iri(target)
        graph.add((subj, pred, iri))
        if iri not in resource_labels:
            resource_labels[iri] = target
        wrote = True
    return wrote


def emit_mixed(graph: Graph, subj, pred, raw: str, keep_literal_if_links: bool = False, resource_labels: dict = None):
    if not raw or resource_labels is None:
        return False
    raw = raw.strip()
    wrote = False

    if pred == SCHEMA.url:
        cleaned_url = clean_value(raw)
        if cleaned_url:
            graph.add((subj, pred, Literal(cleaned_url, datatype=XSD.string)))
            return True
        return False

    if pred in LITERAL_ONLY_PROPS:
        is_timeline = pred == KGONT.timeline or pred == KGONT.chronology

        text = re.sub(r"\[\[([^]|]+)\|([^]]+)\]\]", r"\2", raw)
        text = re.sub(r"\[\[([^]]+)\]\]", r"\1", text)
        for part in split_multi(text, preserve_timeline=is_timeline):
            if part:
                wrote |= emit_literal(graph, subj, pred, part, preserve_timeline=is_timeline)
        return wrote

    has_links = bool(LINK_RE.search(raw))
    if has_links:
        wrote |= emit_links(graph, subj, pred, raw, resource_labels)
        if keep_literal_if_links:
            text = re.sub(r"\[\[([^]|]+)\|([^]]+)\]\]", r"\2", raw)
            text = re.sub(r"\[\[([^]]+)\]\]", r"\1", text)
            wrote |= emit_literal(graph, subj, pred, text)
    else:
        for part in split_multi(raw):
            wrote |= emit_literal(graph, subj, pred, part)
    return wrote


def map_predicate(key: str):
    norm = normalize_key(key)
    if norm in PROPERTY_MAP:
        return PROPERTY_MAP[norm]
    fallback = sanitize_local(norm.replace(" ", "_"))
    return KGONT[fallback]


def materialize_resources(graph: Graph, main_subjects: set, resource_labels: dict):
    """Add rdfs:label for all resources; rdf:type only for main subjects."""
    for iri, label in resource_labels.items():
        graph.add((iri, RDFS.label, Literal(label, datatype=XSD.string)))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    g = Graph()
    g.bind("kg-ont", KGONT, override=True)
    g.bind("kg-res", KGRES, override=True)
    g.bind("rdfs", RDFS, override=True)
    g.bind("schema", SCHEMA, override=True)

    resource_labels = {}
    main_subjects = set()

    for fname in os.listdir(INPUT_DIR):
        if not (fname.startswith("infobox_") and fname.endswith(".txt")):
            continue
        with open(os.path.join(INPUT_DIR, fname), encoding="utf-8") as f:
            full_text = f.read()
        if not full_text:
            continue
        lines = full_text.split("\n")
        entity = lines[0].replace("---", "").strip()
        infobox_text = "\n".join(lines[1:])
        tpl_name, data = parse_infobox_text(infobox_text)
        subj = to_res_iri(entity)
        rdf_type = choose_type(tpl_name, data)
        g.add((subj, RDF.type, rdf_type))

        main_subjects.add(subj)
        resource_labels[subj] = entity

        name_val = data.get("name") or entity
        emit_literal(g, subj, SCHEMA.name, name_val)

        for key, raw_val in data.items():
            if not raw_val or key == "name":
                continue
            pred = map_predicate(key)
            is_other = pred == KGONT.other_names

            if is_other and ("see below" in raw_val.lower() or "see [[" in raw_val.lower()):
                extracted = extract_other_names_section(full_text)
                if extracted:
                    for other_name in extracted:
                        emit_literal(g, subj, pred, other_name)
                    continue

            keep_literal = is_other
            emit_mixed(g, subj, pred, raw_val, keep_literal_if_links=keep_literal, resource_labels=resource_labels)

    materialize_resources(g, main_subjects, resource_labels)

    g.serialize(destination=OUTPUT_FILE, format="turtle")

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if "@prefix schema1:" in content:
        content = content.replace("@prefix schema1:", "@prefix schema:")
        content = content.replace("schema1:", "schema:")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK. RDF generated: {OUTPUT_FILE} ({len(g)} triples)")
    print(f"    - Main subjects: {len(main_subjects)}")
    print(f"    - Materialized resources: {len(resource_labels)}")


if __name__ == "__main__":
    main()

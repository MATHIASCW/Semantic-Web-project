"""
SPARQL queries and Fuseki integration.
"""
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Optional, Dict, List


FUSEKI_URL = "http://localhost:3030/kg-tolkiengateway/sparql"


def build_iri(name: str, base: str) -> str:
    """
    Build an IRI from a name by replacing spaces and dashes.
    """
    safe = name.replace(' ', '_').replace('-', '_')
    return f"{base}{safe}"


def get_resource_by_name_or_iri(resource_name: str) -> Optional[str]:
    """
    Find a resource URI by name/label or direct IRI guess.
    Returns the resource URI if found, None otherwise.
    """
    sparql = SPARQLWrapper(FUSEKI_URL)
    name_predicates = [
        "http://schema.org/name",
        "http://www.w3.org/2000/01/rdf-schema#label",
        "http://tolkien-kg.org/ontology/name",
    ]
    predicates_values = " ".join(f"<{p}>" for p in name_predicates)

    label_candidate = resource_name.replace("_", " ").replace("-", " ")
    safe_label = label_candidate.replace('"', '\"')

    query_labels = f'''
        SELECT ?s WHERE {{
            VALUES ?p {{ {predicates_values} }}
            ?s ?p ?name .
            FILTER(LCASE(STR(?name)) = LCASE("{safe_label}"))
        }} LIMIT 1
    '''
    sparql.setQuery(query_labels)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            return results["results"]["bindings"][0]["s"]["value"]
    except Exception:
        pass

    local_candidate = resource_name.replace(" ", "_").replace("-", "_")
    safe_local = local_candidate.replace('"', '\"')

    query_local = f'''
        SELECT ?s WHERE {{
            VALUES ?base {{ "http://tolkien-kg.org/resource/" "http://tolkien-kg.org/ontology/" "http://tolkien-kg.org/card/" }}
            ?s ?p ?o .
            FILTER(STRSTARTS(STR(?s), ?base))
            BIND(STRAFTER(STR(?s), ?base) AS ?local)
            FILTER(LCASE(?local) = LCASE("{safe_local}"))
        }} LIMIT 1
    '''
    sparql.setQuery(query_local)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            return results["results"]["bindings"][0]["s"]["value"]
    except Exception:
        pass

    iri_guesses = [
        build_iri(resource_name, "http://tolkien-kg.org/resource/"),
        build_iri(resource_name, "http://tolkien-kg.org/ontology/"),
        build_iri(resource_name, "http://tolkien-kg.org/card/"),
    ]

    for iri in iri_guesses:
        sparql.setQuery(f'''ASK {{ <{iri}> ?p ?o }}''')
        try:
            exists = sparql.query().convert().get('boolean', False)
            if exists:
                return iri
        except Exception:
            pass

    return None


def get_resource_properties(subject_uri: str) -> Optional[Dict[str, List[str]]]:
    """Fetch all properties of a resource by its URI (incoming + outgoing, sameAs-aware)."""
    sparql = SPARQLWrapper(FUSEKI_URL)

    sparql.setQuery(f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?p ?o ?dir WHERE {{
            {{
                ?equiv (owl:sameAs|^owl:sameAs)* <{subject_uri}> .
                ?equiv ?p ?o .
                BIND("out" AS ?dir)
            }}
            UNION
            {{
                ?equiv (owl:sameAs|^owl:sameAs)* <{subject_uri}> .
                ?s ?p ?equiv .
                BIND(?s AS ?o)
                BIND("in" AS ?dir)
            }}
        }}
    """)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        props = {}

        for binding in results["results"]["bindings"]:
            pred = binding["p"]["value"]
            obj = binding["o"]["value"]
            if binding["o"].get("type") == "literal":
                lang = binding["o"].get("xml:lang")
                if lang:
                    obj = f"{obj}||lang:{lang}"
            direction = binding.get("dir", {}).get("value", "out")
            if direction == "in":
                pred = f"^{pred}"
            if pred not in props:
                props[pred] = []
            props[pred].append(obj)

        return props
    except Exception:
        return None

def get_ontology_property_info(name_or_uri: str) -> Optional[Dict[str, str]]:
    """Fetch ontology property info (label, comment, type, domain, range) from Fuseki.
    Accepts either local name (e.g., 'affiliation') or full URI.
    """
    if name_or_uri.startswith("http://") or name_or_uri.startswith("https://"):
        iri = name_or_uri
    else:
        iri = f"http://tolkien-kg.org/ontology/{name_or_uri}"

    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(f'''
        SELECT ?type ?label ?comment ?domain ?range WHERE {{
            OPTIONAL {{ <{iri}> a ?type }}
            OPTIONAL {{ <{iri}> <http://www.w3.org/2000/01/rdf-schema#label> ?label }}
            OPTIONAL {{ <{iri}> <http://www.w3.org/2000/01/rdf-schema#comment> ?comment }}
            OPTIONAL {{ <{iri}> <http://www.w3.org/2000/01/rdf-schema#domain> ?domain }}
            OPTIONAL {{ <{iri}> <http://www.w3.org/2000/01/rdf-schema#range> ?range }}
        }} LIMIT 1
    ''')
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]
        info = {"uri": iri}
        if bindings:
            b = bindings[0]
            for key in ("type", "label", "comment", "domain", "range"):
                if key in b:
                    info[key] = b[key]["value"]
        return info
    except Exception:
        return None


def get_characters_list(limit: int = 100) -> List[str]:
    """
    Returns a list of character names from the knowledge graph.
    """
    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(f'''
        SELECT ?name WHERE {{
            ?s <http://schema.org/name> ?name .
        }} LIMIT {limit}
    ''')
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return [r["name"]["value"] for r in results["results"]["bindings"]]
    except Exception:
        return []


def get_character_by_name(name: str) -> Optional[List[Dict]]:
    """Returns information about a character by their exact name."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(f'''
        SELECT ?p ?o WHERE {{
            ?s <http://schema.org/name> "{name}" .
            ?s ?p ?o .
        }}
    ''')
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return [
            {"property": r["p"]["value"], "value": r["o"]["value"]}
            for r in results["results"]["bindings"]
        ]
    except Exception:
        return None


def get_statistics() -> Dict[str, int]:
    """Returns global statistics of the knowledge graph."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    
    stats = {
        'total': 0,
        'characters': 0,
        'locations': 0,
        'works': 0
    }
    
    sparql.setQuery('''
        SELECT (COUNT(DISTINCT ?s) AS ?count) WHERE {
            ?s a ?type .
            ?s <http://schema.org/name> ?name .
            FILTER(
                STRSTARTS(STR(?type), "http://tolkien-kg.org/ontology/") ||
                STRSTARTS(STR(?type), "http://schema.org/")
            )
        }
    ''')
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        count = results["results"]["bindings"][0]["count"]["value"]
        stats['total'] = int(count)
    except Exception:
        pass
    
    sparql.setQuery('''
        SELECT (COUNT(DISTINCT ?s) AS ?count) WHERE {
            ?s a <http://tolkien-kg.org/ontology/Character> .
            ?s <http://schema.org/name> ?name .
        }
    ''')
    
    try:
        results = sparql.query().convert()
        count = results["results"]["bindings"][0]["count"]["value"]
        stats['characters'] = int(count)
    except Exception:
        pass
    
    sparql.setQuery('''
        SELECT (COUNT(DISTINCT ?s) AS ?count) WHERE {
            ?s a <http://tolkien-kg.org/ontology/Location> .
            ?s <http://schema.org/name> ?name .
        }
    ''')
    
    try:
        results = sparql.query().convert()
        count = results["results"]["bindings"][0]["count"]["value"]
        stats['locations'] = int(count)
    except Exception:
        pass
    
    sparql.setQuery('''
        SELECT (COUNT(DISTINCT ?s) AS ?count) WHERE {
            ?s a <http://schema.org/CreativeWork> .
            ?s <http://schema.org/name> ?name .
        }
    ''')
    
    try:
        results = sparql.query().convert()
        count = results["results"]["bindings"][0]["count"]["value"]
        stats['works'] = int(count)
    except Exception:
        pass
    
    return stats


def _resolve_type_iri(type_name: str) -> str:
    """Return a full IRI for a given type name or IRI."""
    if not type_name:
        return ""
    if type_name.startswith("http://") or type_name.startswith("https://"):
        return type_name

    aliases = {
        "Character": "http://tolkien-kg.org/ontology/Character",
        "Location": "http://tolkien-kg.org/ontology/Location",
        "Work": "http://schema.org/CreativeWork",
        "Organization": "http://tolkien-kg.org/ontology/Organization",
        "Artifact": "http://tolkien-kg.org/ontology/Artifact",
        "Race": "http://tolkien-kg.org/ontology/Race",
        "Event": "http://tolkien-kg.org/ontology/Event",
        "Object": "http://tolkien-kg.org/ontology/Object",
    }
    if type_name in aliases:
        return aliases[type_name]

    return f"http://tolkien-kg.org/ontology/{type_name}"


def get_entity_type_facets() -> list[dict]:
    """Return available entity types with counts for filter UI."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(
        """
        SELECT ?type (COUNT(DISTINCT ?s) AS ?count) WHERE {
            ?s a ?type .
            ?s <http://schema.org/name> ?name .
            FILTER(
                STRSTARTS(STR(?type), "http://tolkien-kg.org/ontology/") ||
                STRSTARTS(STR(?type), "http://schema.org/")
            )
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        LIMIT 20
        """
    )
    sparql.setReturnFormat(JSON)

    facets = []
    try:
        results = sparql.query().convert()
        for row in results["results"]["bindings"]:
            facets.append(
                {
                    "type": row["type"]["value"],
                    "count": int(row["count"]["value"]),
                }
            )
    except Exception:
        pass

    return facets


def get_entities_by_type(
    entity_type: str = None, limit: int = 20, offset: int = 0, search_query: str = None
) -> tuple:
    """
    Returns: (entities_list, total_count, type_facets)
    entities_list: list of dicts {name, uri, type}
    """
    sparql = SPARQLWrapper(FUSEKI_URL)

    type_filter = "?s a ?type ."
    type_iri = _resolve_type_iri(entity_type) if entity_type else ""
    if type_iri:
        type_filter = f"?s a <{type_iri}> ."

    if search_query:
        safe_query = search_query.replace('"', '\"')
        search_filter = f'''
            ?s <http://schema.org/name> ?name .
            FILTER(CONTAINS(LCASE(?name), LCASE("{safe_query}")))
        '''
    else:
        search_filter = "?s <http://schema.org/name> ?name ."

    count_query = f'''
        SELECT (COUNT(DISTINCT ?s) AS ?count) WHERE {{
            {type_filter}
            {search_filter}
        }}
    '''

    sparql.setQuery(count_query)
    sparql.setReturnFormat(JSON)

    total_count = 0
    try:
        results = sparql.query().convert()
        total_count = int(results["results"]["bindings"][0]["count"]["value"])
    except Exception:
        pass

    query = f'''
        SELECT DISTINCT ?s ?name ?type WHERE {{
            {type_filter}
            {search_filter}
            ?s a ?type .
        }}
        ORDER BY ?name
        LIMIT {limit}
        OFFSET {offset}
    '''

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    entities = []
    try:
        results = sparql.query().convert()
        for binding in results["results"]["bindings"]:
            entity = {
                "name": binding["name"]["value"],
                "uri": binding["s"]["value"],
                "type": binding["type"]["value"],
            }
            entities.append(entity)
    except Exception:
        pass

    type_facets = get_entity_type_facets()

    return entities, total_count, type_facets


def get_related_cards(subject_uri: str) -> List[Dict[str, str]]:
    """Return related METW card info (label, image) for a resource."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(f"""
        PREFIX schema: <http://schema.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?card ?label ?image WHERE {{
            {{
                <{subject_uri}> schema:subjectOf ?card .
            }}
            UNION
            {{
                ?card schema:about <{subject_uri}> .
            }}
            OPTIONAL {{
                ?card rdfs:label ?label .
                FILTER(lang(?label) = "" || lang(?label) = "en")
            }}
            OPTIONAL {{ ?card schema:image ?image . }}
        }}
    """)
    sparql.setReturnFormat(JSON)

    cards = {}
    try:
        results = sparql.query().convert()
        for binding in results["results"]["bindings"]:
            card_uri = binding["card"]["value"]
            entry = cards.setdefault(card_uri, {"uri": card_uri, "label": None, "image": None})
            if "label" in binding and not entry["label"]:
                entry["label"] = binding["label"]["value"]
            if "image" in binding and not entry["image"]:
                entry["image"] = binding["image"]["value"]
    except Exception:
        return []

    return list(cards.values())

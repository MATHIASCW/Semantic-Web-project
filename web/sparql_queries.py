"""
SPARQL queries and Fuseki integration.
"""
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Optional, Dict, List


FUSEKI_URL = "http://localhost:3030/kg-tolkiengateway/sparql"


def build_iri(name: str, base: str) -> str:
    """Construit un IRI à partir d'un nom en remplaçant espaces et tirets."""
    safe = name.replace(' ', '_').replace('-', '_')
    return f"{base}{safe}"


def get_resource_by_name_or_iri(resource_name: str) -> Optional[str]:
    """
    Find a resource URI by name/label or direct IRI guess.
    Returns the resource URI if found, None otherwise.
    """
    sparql = SPARQLWrapper(FUSEKI_URL)
    # 1) Try case-insensitive match on labels (schema:name, rdfs:label, kg-ont:name)
    name_predicates = [
        "http://schema.org/name",
        "http://www.w3.org/2000/01/rdf-schema#label",
        "http://tolkien-kg.org/ontology/name",
    ]
    predicates_values = " ".join(f"<{p}>" for p in name_predicates)

    # Replace underscores/hyphens with spaces for label matching
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

    # 2) Try case-insensitive match on local name part of subject IRI
    local_candidate = resource_name.replace(" ", "_").replace("-", "_")
    safe_local = local_candidate.replace('"', '\"')

    query_local = f'''
        SELECT ?s WHERE {{
            VALUES ?base {{ "http://tolkien-kg.org/resource/" "http://tolkien-kg.org/ontology/" }}
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

    # 3) Fallback: direct IRI guesses (as-is)
    iri_guesses = [
        build_iri(resource_name, "http://tolkien-kg.org/resource/"),
        build_iri(resource_name, "http://tolkien-kg.org/ontology/"),
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
    """Fetch all properties of a resource by its URI."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    
    sparql.setQuery(f'''
        SELECT ?p ?o WHERE {{
            <{subject_uri}> ?p ?o .
        }}
    ''')
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        props = {}
        
        for binding in results["results"]["bindings"]:
            pred = binding["p"]["value"]
            obj = binding["o"]["value"]
            if pred not in props:
                props[pred] = []
            props[pred].append(obj)
        
        return props
    except Exception:
        return None


def get_characters_list(limit: int = 100) -> List[str]:
    """Retourne une liste de noms de personnages du knowledge graph."""
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
    """Retourne les infos d'un personnage par son nom exact."""
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

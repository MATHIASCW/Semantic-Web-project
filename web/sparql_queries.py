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
        }
    ''')
    
    try:
        results = sparql.query().convert()
        count = results["results"]["bindings"][0]["count"]["value"]
        stats['works'] = int(count)
    except Exception:
        pass
    
    return stats


def get_entities_by_type(entity_type: str = None, limit: int = 20, offset: int = 0, 
                        search_query: str = None) -> tuple:
    """
    Returns a list of entities filtered by type with pagination.
    
    Returns:
        (entities_list, total_count) where entities_list is list of dicts with name, uri, type
    """
    sparql = SPARQLWrapper(FUSEKI_URL)
    
    type_filter = ""
    if entity_type == 'Character':
        type_filter = '?s a <http://tolkien-kg.org/ontology/Character> .'
    elif entity_type == 'Location':
        type_filter = '?s a <http://tolkien-kg.org/ontology/Location> .'
    elif entity_type == 'Work':
        type_filter = '?s a <http://schema.org/CreativeWork> .'
    else:
        type_filter = '?s a ?type .'
    
    search_filter = ""
    if search_query:
        safe_query = search_query.replace('"', '\\"')
        search_filter = f'''
            ?s <http://schema.org/name> ?name .
            FILTER(CONTAINS(LCASE(?name), LCASE("{safe_query}")))
        '''
    else:
        search_filter = '?s <http://schema.org/name> ?name .'
    
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
                'name': binding['name']['value'],
                'uri': binding['s']['value'],
                'type': binding['type']['value']
            }
            entities.append(entity)
    except Exception:
        pass
    
    return entities, total_count

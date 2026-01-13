from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse

from web.models import ResourceData
from web.sparql_queries import (
    get_resource_by_name_or_iri,
    get_resource_properties,
    get_characters_list,
    get_character_by_name,
    get_statistics,
    get_entities_by_type,
    get_ontology_property_info,
    get_related_cards,
)
from web.html_renderer import (
    generate_html_page,
    generate_turtle_for_resource,
    generate_ontology_property_page,
    generate_turtle_for_property,
)
from web.home_renderer import generate_home_page, generate_browse_page

"""
Tolkien Knowledge Graph API
A FastAPI-based REST API for querying a Tolkien-themed RDF knowledge graph
stored in Apache Jena Fuseki. Provides endpoints to retrieve character information
from the knowledge graph using SPARQL queries.

Architecture:
    - main.py: FastAPI routes only
    - models.py: Data structures (ResourceData, TimelineEvent, etc.)
    - sparql_queries.py: All SPARQL queries and Fuseki integration
    - html_renderer.py: HTML page generation and content formatting

Features:
    - CORS enabled for cross-origin requests
    - Character listing with configurable limits
    - Character detail lookup by name
    - Content negotiation (HTML, JSON, Turtle/RDF)
    - Error handling with appropriate HTTP status codes

Configuration:
    - Fuseki Endpoint: http://localhost:3030/kg-tolkiengateway/sparql
    - API Version: 1.0
    - Default result limit: 100 characters (max: 500)

Dependencies:
    - FastAPI: Web framework
    - SPARQLWrapper: SPARQL query interface
    - CORS Middleware: Cross-origin resource sharing support
"""

app = FastAPI(
    title="Tolkien KG API",
    description="API pour interroger Fuseki avec FastAPI",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    """Generate the home page with global statistics."""
    stats = get_statistics()
    html = generate_home_page(stats)
    return HTMLResponse(html)


@app.get("/characters", tags=["Characters"])
def list_characters(limit: int = Query(100, ge=1, le=500)):
    """Returns a list of character names from the knowledge graph."""
    names = get_characters_list(limit)
    return {"count": len(names), "characters": names}


@app.get("/browse", tags=["Browse"])
def browse_entities(
    type: str = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    search: str = Query(None, alias="search"),
):
    """
    Interactive browsing page to explore entities.

    Query params:
    - type: Character, Location, Work (optional)
    - page: page number (default: 1)
    - search: search term (optional)
    """
    items_per_page = 20
    offset = (page - 1) * items_per_page

    entities, total_count = get_entities_by_type(
        entity_type=type,
        limit=items_per_page,
        offset=offset,
        search_query=search,
    )

    total_pages = (total_count + items_per_page - 1) // items_per_page
    if total_pages == 0:
        total_pages = 1

    html = generate_browse_page(
        entities=entities,
        entity_type=type,
        page=page,
        total_pages=total_pages,
        search_query=search,
    )

    return HTMLResponse(html)


@app.get("/character/{name}", tags=["Characters"])
def get_character(name: str):
    """Returns information about a character by their exact name."""
    props = get_character_by_name(name)
    if not props:
        return JSONResponse(status_code=404, content={"error": f"No character found for '{name}'"})
    return {"name": name, "properties": props}


@app.get("/resource/{name}", tags=["Linked Data"])
async def get_resource(name: str, request: Request, format: str = Query(None, alias="format")):
    """
    Linked Data endpoint - Dereference a resource and return its description.

    Content-Negotiation:
    - Accept: text/turtle -> Turtle/RDF
    - Accept: application/json -> JSON
    - Accept: text/html -> HTML (par defaut)

    Query param 'format' peut override: ?format=turtle, ?format=json, ?format=html
    """

    resource_uri = get_resource_by_name_or_iri(name)
    if not resource_uri:
        return JSONResponse(status_code=404, content={"error": f"Ressource '{name}' non trouvee"})

    canonical_name = name
    try:
        canonical = resource_uri.rsplit("/", 1)[-1]
        if canonical != name:
            suffix = ""
            if format:
                suffix = f"?format={format}"
            canonical_name = canonical
            return HTMLResponse(status_code=307, content="", headers={"Location": f"/resource/{canonical}{suffix}"})
        canonical_name = canonical
    except Exception:
        pass

    properties = get_resource_properties(resource_uri)
    if not properties:
        return JSONResponse(status_code=404, content={"error": f"Ressource '{name}' non trouvee"})

    related_cards = get_related_cards(resource_uri)
    resource = ResourceData(name=name, uri=resource_uri, properties=properties)

    # Default: Turtle (machine-readable). HTML only when explicitly asked via format=html.
    accept_header = request.headers.get("accept", "text/turtle").lower()

    # Explicit format overrides headers
    if format:
        fmt = format.lower()
        if fmt == "turtle":
            content = generate_turtle_for_resource(resource)
            return PlainTextResponse(content, media_type="text/turtle")
        if fmt == "json":
            return JSONResponse(
                {"name": resource.name, "uri": resource.uri, "properties": resource.properties}
            )
        if fmt == "html":
            return RedirectResponse(url=f"/page/{canonical_name}", status_code=303)

    # Header-driven negotiation (only JSON honored automatically)
    if "application/json" in accept_header or "application/ld+json" in accept_header:
        return JSONResponse({"name": resource.name, "uri": resource.uri, "properties": resource.properties})

    # Default fallback: Turtle (even if browser asked HTML but no format param)
    content = generate_turtle_for_resource(resource)
    return PlainTextResponse(content, media_type="text/turtle")


@app.get("/page/{name}", tags=["Linked Data"])
def get_page(name: str):
    """HTML page endpoint (DBpedia-style)."""
    resource_uri = get_resource_by_name_or_iri(name)
    if not resource_uri:
        return HTMLResponse("<h1>Ressource non trouvee</h1>", status_code=404)

    properties = get_resource_properties(resource_uri)
    if not properties:
        return HTMLResponse("<h1>Ressource non trouvee</h1>", status_code=404)

    related_cards = get_related_cards(resource_uri)
    resource = ResourceData(name=name, uri=resource_uri, properties=properties)
    html = generate_html_page(resource, related_cards=related_cards)
    return HTMLResponse(html)


@app.get("/ontology/{name}", tags=["Ontology"])
def get_ontology_property(name: str, request: Request, format: str = Query(None, alias="format")):
    """Serve a local documentation page for ontology properties (kg-ont)."""
    iri = f"http://tolkien-kg.org/ontology/{name}"
    info = get_ontology_property_info(iri)
    if not info:
        return HTMLResponse("<h1>Ontology property not found</h1>", status_code=404)

    accept_header = request.headers.get("accept", "text/html").lower()

    if format:
        if format.lower() == "turtle":
            content = generate_turtle_for_property(info)
            return PlainTextResponse(content, media_type="text/turtle")
        if format.lower() == "json":
            return JSONResponse(info)
        if format.lower() == "html":
            html = generate_ontology_property_page(info)
            return HTMLResponse(html)

    if "application/json" in accept_header or "application/ld+json" in accept_header:
        return JSONResponse(info)
    if "text/turtle" in accept_header or "application/rdf+turtle" in accept_header:
        content = generate_turtle_for_property(info)
        return PlainTextResponse(content, media_type="text/turtle")

    html = generate_ontology_property_page(info)
    return HTMLResponse(html)


@app.get("/favicon.ico")
def favicon():
    return PlainTextResponse("", media_type="image/x-icon")

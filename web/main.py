
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

from web.models import ResourceData
from web.sparql_queries import (
    get_resource_by_name_or_iri,
    get_resource_properties,
    get_characters_list,
    get_character_by_name,
    get_statistics,
    get_entities_by_type,
)
from web.html_renderer import generate_html_page, generate_turtle_for_resource
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

Author: mathias
Location: ../Semantic-Web-project/web/main.py
"""

app = FastAPI(title="Tolkien KG API", description="API pour interroger Fuseki avec FastAPI", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def root():
    """Page d'accueil - Affiche les statistiques et catégories."""
    stats = get_statistics()
    html = generate_home_page(stats)
    return HTMLResponse(html)

@app.get("/characters", tags=["Characters"])
def list_characters(limit: int = Query(100, ge=1, le=500)):
    """Retourne une liste de personnages (noms) du knowledge graph."""
    names = get_characters_list(limit)
    return {"count": len(names), "characters": names}


@app.get("/browse", tags=["Browse"])
def browse_entities(
    type: str = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    search: str = Query(None, alias="search")
):
    """
    Page de navigation interactive pour parcourir les entités.
    
    Query params:
    - type: Character, Location, Work (optionnel)
    - page: numéro de page (défaut: 1)
    - search: terme de recherche (optionnel)
    """
    ITEMS_PER_PAGE = 20
    offset = (page - 1) * ITEMS_PER_PAGE
    
    entities, total_count = get_entities_by_type(
        entity_type=type,
        limit=ITEMS_PER_PAGE,
        offset=offset,
        search_query=search
    )
    
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if total_pages == 0:
        total_pages = 1
    
    html = generate_browse_page(
        entities=entities,
        entity_type=type,
        page=page,
        total_pages=total_pages,
        search_query=search
    )
    
    return HTMLResponse(html)

@app.get("/character/{name}", tags=["Characters"])
def get_character(name: str):
    """Retourne les infos d'un personnage par son nom exact."""
    props = get_character_by_name(name)
    if not props:
        return JSONResponse(status_code=404, content={"error": f"Aucun personnage trouvé pour '{name}'"})
    return {"name": name, "properties": props}

@app.get("/resource/{name}", tags=["Linked Data"])
async def get_resource(name: str, request: Request, format: str = Query(None, alias="format")):
    """
    Endpoint Linked Data - Dereference une ressource et retourne sa description.
    
    Content-Negotiation:
    - Accept: text/turtle → Turtle/RDF
    - Accept: application/json → JSON
    - Accept: text/html → HTML (par défaut)
    
    Query param 'format' peut override: ?format=turtle, ?format=json, ?format=html
    """
    
    resource_uri = get_resource_by_name_or_iri(name)
    if not resource_uri:
        return JSONResponse(
            status_code=404,
            content={"error": f"Ressource '{name}' non trouvée"}
        )

    try:
        canonical = resource_uri.rsplit('/', 1)[-1]
        if canonical != name:
            suffix = ""
            if format:
                suffix = f"?format={format}"
            return HTMLResponse(status_code=307, content="", headers={"Location": f"/resource/{canonical}{suffix}"})
    except Exception:
        pass
    
    properties = get_resource_properties(resource_uri)
    if not properties:
        return JSONResponse(
            status_code=404,
            content={"error": f"Ressource '{name}' non trouvée"}
        )
    
    resource = ResourceData(name=name, uri=resource_uri, properties=properties)
    
    accept_header = request.headers.get("accept", "text/html").lower()
    
    if format:
        if format.lower() == "turtle":
            content = generate_turtle_for_resource(resource)
            return PlainTextResponse(content, media_type="text/turtle")
        elif format.lower() == "json":
            return JSONResponse({
                "name": resource.name,
                "uri": resource.uri,
                "properties": resource.properties
            })
        elif format.lower() == "html":
            html = generate_html_page(resource)
            return HTMLResponse(html)
    
    if "application/json" in accept_header or "application/ld+json" in accept_header:
        return JSONResponse({
            "name": resource.name,
            "uri": resource.uri,
            "properties": resource.properties
        })
    elif "text/turtle" in accept_header or "application/rdf+turtle" in accept_header:
        content = generate_turtle_for_resource(resource)
        return PlainTextResponse(content, media_type="text/turtle")
    else:
        html = generate_html_page(resource)
        return HTMLResponse(html)


@app.get("/page/{name}", tags=["Linked Data"])
def get_page(name: str):
    """HTML page endpoint (DBpedia-style)."""
    resource_uri = get_resource_by_name_or_iri(name)
    if not resource_uri:
        return HTMLResponse("<h1>Ressource non trouvée</h1>", status_code=404)
    
    properties = get_resource_properties(resource_uri)
    if not properties:
        return HTMLResponse("<h1>Ressource non trouvée</h1>", status_code=404)
    
    resource = ResourceData(name=name, uri=resource_uri, properties=properties)
    html = generate_html_page(resource)
    return HTMLResponse(html)


@app.get("/favicon.ico")
def favicon():
    return PlainTextResponse("", media_type="image/x-icon")
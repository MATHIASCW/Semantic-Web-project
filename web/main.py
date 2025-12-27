
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from SPARQLWrapper import SPARQLWrapper, JSON

"""
Tolkien Knowledge Graph API
A FastAPI-based REST API for querying a Tolkien-themed RDF knowledge graph
stored in Apache Jena Fuseki. Provides endpoints to retrieve character information
from the knowledge graph using SPARQL queries.
Features:
    - CORS enabled for cross-origin requests
    - Character listing with configurable limits
    - Character detail lookup by name
    - Error handling with appropriate HTTP status codes
    - SPARQL query execution against Fuseki endpoint
Configuration:
    - Fuseki Endpoint: http://localhost:3030/kg-tolkiengateway/sparql
    - API Version: 1.0
    - Default result limit: 100 characters (max: 500)
Dependencies:
    - FastAPI: Web framework
    - SPARQLWrapper: SPARQL query interface
    - CORS Middleware: Cross-origin resource sharing support
Author: mathi
Location: /c:/Users/mathi/Documents/GitHub/Semantic-Web-project/web/main.py
"""

app = FastAPI(title="Tolkien KG API", description="API pour interroger Fuseki avec FastAPI", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FUSEKI_URL = "http://localhost:3030/kg-tolkiengateway/sparql"

@app.get("/", tags=["Root"])
def root():
    """Bienvenue sur l'API Tolkien Knowledge Graph."""
    return {"message": "Bienvenue sur l'API Tolkien Knowledge Graph. Voir /docs pour la documentation."}

@app.get("/characters", tags=["Characters"])
def get_characters(limit: int = Query(100, ge=1, le=500)):
    """Retourne une liste de personnages (noms) du knowledge graph."""
    sparql = SPARQLWrapper(FUSEKI_URL)
    sparql.setQuery(f'''
        SELECT ?name WHERE {{
            ?s <http://schema.org/name> ?name .
        }} LIMIT {limit}
    ''')
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        names = [r["name"]["value"] for r in results["results"]["bindings"]]
        return {"count": len(names), "characters": names}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/character/{name}", tags=["Characters"])
def get_character_by_name(name: str):
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
        props = [
            {"property": r["p"]["value"], "value": r["o"]["value"]}
            for r in results["results"]["bindings"]
        ]
        if not props:
            return JSONResponse(status_code=404, content={"error": f"Aucun personnage trouvé pour '{name}'"})
        return {"name": name, "properties": props}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
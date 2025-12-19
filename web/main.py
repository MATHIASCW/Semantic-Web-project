from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
import os
from urllib.parse import quote

app = FastAPI()

# Dossier des templates HTML
templates = Jinja2Templates(directory="web/templates")

DEFAULT_DATASET = os.getenv("FUSEKI_DATASET", "kg-tolkiengateway")
SPARQL_ENDPOINT = os.getenv(
    "SPARQL_ENDPOINT",
    f"http://localhost:3030/{DEFAULT_DATASET}/sparql",
)
BASE_URI = os.getenv("BASE_URI", "https://yourkg.org/resource/")

def make_uri(label: str) -> str:
    safe = quote(label.replace(" ", "_"), safe="_-~()'")
    return f"{BASE_URI}{safe}"

def build_construct_query(uri: str) -> str:
    return f"""
PREFIX owl: <http://www.w3.org/2002/07/owl#>
CONSTRUCT {{
  ?s ?p ?o .
  ?x ?p2 ?s .
}}
WHERE {{
  {{
    ?s (owl:sameAs|^owl:sameAs)? <{uri}> .
    ?s ?p ?o .
  }}
  UNION
  {{
    ?s (owl:sameAs|^owl:sameAs)? <{uri}> .
    ?x ?p2 ?s .
  }}
}}
"""

def sparql_construct(uri: str) -> bytes:
    import requests
    query = build_construct_query(uri)
    resp = requests.post(
        SPARQL_ENDPOINT,
        data={"query": query},
        headers={"Accept": "text/turtle"},
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"SPARQL error {resp.status_code}: {resp.text[:200]}")
    return resp.content

def sparql_sample_labels(limit: int = 12):
    import requests
    query = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?label WHERE {{
  ?s rdfs:label ?label .
}}
LIMIT {limit}
"""
    resp = requests.post(
        SPARQL_ENDPOINT,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=20,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"SPARQL error {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    return [b["label"]["value"] for b in data.get("results", {}).get("bindings", [])]

def ttl_to_html(uri: str, ttl_bytes: bytes) -> str:
    import rdflib
    g = rdflib.Graph()
    g.parse(data=ttl_bytes.decode("utf-8", errors="replace"), format="turtle")

    label = None
    image = None
    rows = []
    for s, p, o in g:
        if str(s) != uri:
            continue
        p_str = str(p)
        o_str = str(o)
        if p_str.endswith("label") and not label:
            label = o_str
        if p_str.endswith("image") and not image:
            image = o_str
        rows.append((p_str, o_str))
    rows.sort()
    title = label or uri
    return {
        "title": title,
        "uri": uri,
        "image": image,
        "rows": rows,
    }

@app.get("/test/page1", response_class=HTMLResponse)
async def page1(request: Request):
    return templates.TemplateResponse(
        "page1.html",
        {"request": request}
    )

@app.get("/test/page2", response_class=HTMLResponse)
async def page2(request: Request):
    return templates.TemplateResponse(
        "page2.html",
        {"request": request}
    )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        sample_labels = sparql_sample_labels()
    except Exception:
        sample_labels = [
            "Elrond",
            "Gandalf",
            "Aragorn",
            "The Shire",
            "Mordor",
        ]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sample_labels": sample_labels,
        },
    )

def render_entity(label: str, request: Request):
    uri = make_uri(label)
    try:
        ttl = sparql_construct(uri)
    except Exception as exc:
        return HTMLResponse(
            content=f"<h1>SPARQL error</h1><pre>{exc}</pre>",
            status_code=500,
        )
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        data = ttl_to_html(uri, ttl)
        return templates.TemplateResponse(
            "entity.html",
            {"request": request, **data},
        )
    return Response(content=ttl, media_type="text/turtle")

@app.get("/resource")
async def resource_query(label: str = "", request: Request = None):
    if not label:
        return HTMLResponse(content="<h1>Missing label</h1>", status_code=400)
    return render_entity(label, request)

@app.get("/resource/{label}")
async def resource(label: str, request: Request):
    return render_entity(label, request)

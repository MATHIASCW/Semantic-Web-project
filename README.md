# Tolkien Knowledge Graph — Semantic Web Project

A comprehensive Knowledge Graph project built from the Tolkien Gateway wiki, featuring RDF generation, ontology alignment, SHACL validation, external data integration, SPARQL endpoint, and Linked Data interface.

---

## Objective & Scope

Goal: Build a Knowledge Graph (KG) from a wiki source (Tolkien Gateway) and deliver:
- Extraction → transformation of infoboxes into RDF (Turtle)
- Vocabulary alignment with `schema.org` + dedicated ontology (`kg-ont`)
- Multilingual labels where possible
- External links (DBpedia, METW cards, LotR CSV)
- SPARQL endpoint (Fuseki) with queries including implicit facts (property paths)
- Linked Data interface (HTML/Turtle/JSON) via content negotiation
- SHACL validation

---

## Architecture

- Source: Tolkien Gateway pages + infoboxes (wikitext)
- RDF Scripts (rdflib): extraction, normalization, merging, enrichment
- Triplestore: Apache Jena Fuseki (SPARQL 1.1)
- Web: FastAPI (linked data interface + navigation)
- Ontology: `data/rdf/tolkien-kg-ontology.ttl` (aligned with `schema.org`)
- SHACL: `data/rdf/tolkien-shapes.ttl`

Useful directory structure:
- Generated RDF data: `data/rdf/`
- Scripts: `scripts/rdf/`
- Web interface: `web/`

---

## Quick Start

Prerequisites: Python 3.11+, Java (for Fuseki), `curl`.

1) Install dependencies
```bash
pip install -r requirements.txt
```

2) Generate RDF (from infoboxes)
```bash
python scripts/rdf/rdf_maker.py
```
This produces `data/rdf/all_infoboxes.ttl`.

3) Add multilingual labels (optional if you already have a labels file)
```bash
# Merge existing multilingual labels into all_infoboxes_with_lang.ttl
python scripts/rdf/merge_multilang_labels.py
```

4) Integrate external data (METW cards + custom CSV + DBpedia links)
```bash
python scripts/rdf/integrate_external_data.py
```
Generates `data/rdf/external_links.ttl`.

5) Merge everything into final KG file
```bash
python scripts/rdf/merge_all_ttl.py
```
Produces `data/rdf/kg_full.ttl`.

6) Start Fuseki and load the data
```bash
# Launch Fuseki (in-memory) on dataset /kg-tolkiengateway
fuseki-server --mem /kg-tolkiengateway

# Load the final KG
curl -X POST http://localhost:3030/kg-tolkiengateway/data \
    -H "Content-Type: text/turtle" \
    --data-binary @data/rdf/kg_full.ttl
```

7) Launch the web interface
- Windows: `scripts/setup/start_web.bat`
- Linux/Mac: `bash scripts/setup/start_web.sh`

URLs:
- Home: http://localhost:8000/
- Browse: http://localhost:8000/browse
- API Docs (OpenAPI): http://localhost:8000/docs

---

## Detailed Pipeline (step by step)

1) Infobox extraction and parsing
- Input: `data/infoboxes/infobox_*.txt` files (title + wikitext)
- Script: [scripts/rdf/rdf_maker.py](scripts/rdf/rdf_maker.py)
- Key actions:
    - Wikitext cleaning (refs, tags, external links, HTML)
    - Template and type detection (character, location, work…)
    - Field → property mapping (`schema:` and `kg-ont:`)
    - Generation of `schema:name`, internal links → `kg-res:` IRIs
    - Materialization of `rdfs:label` for each referenced resource
    - Prefix normalization (e.g., `schema1:` → `schema:`)
    - Output: `data/rdf/all_infoboxes.ttl`

2) Ontology and alignment
- File: [data/rdf/tolkien-kg-ontology.ttl](data/rdf/tolkien-kg-ontology.ttl)
- Goal: Define `kg-ont:` classes/properties and reuse `schema.org` as much as possible.
- Extension script (optional): [scripts/rdf/extend_ontology.py](scripts/rdf/extend_ontology.py) to add missing detected properties.

3) Multilingual labels
- Source: `data/rdf/multilang_labels.ttl` (pre-generated) + `schema:name`
- Merge: [scripts/rdf/merge_multilang_labels.py](scripts/rdf/merge_multilang_labels.py) → `data/rdf/all_infoboxes_with_lang.ttl`
- Rule: if no `rdfs:label@en`, use `schema:name` as English fallback.

4) External data integration
- Script: [scripts/rdf/integrate_external_data.py](scripts/rdf/integrate_external_data.py)
- Sources:
    - `data/rdf/cards.json` (METW) → `kg-card:` links + labels
    - `data/rdf/lotr_characters.csv` → enrichment (birth/death/gender/race…)
    - `owl:sameAs` alignments to DBpedia when applicable
- Output: `data/rdf/external_links.ttl`
- Note: Automatic prefix normalization `schema1:` → `schema:`.

5) Final KG merge
- Script: [scripts/rdf/merge_all_ttl.py](scripts/rdf/merge_all_ttl.py)
- Inputs: `all_infoboxes_with_lang.ttl`, `external_links.ttl`
- Output: `data/rdf/kg_full.ttl`
- Note: Output prefix normalization.

6) SHACL validation
- Script: [scripts/rdf/validate_final.py](scripts/rdf/validate_final.py)
- Shapes: [data/rdf/tolkien-shapes.ttl](data/rdf/tolkien-shapes.ttl)
- Execution:
```bash
python scripts/rdf/validate_final.py
```

7) Linked Data interface (FastAPI)
- Code: `web/`
- Features:
    - Content negotiation (HTML/Turtle) for entities and properties
    - Pages: Home (stats + type tiles), Browse (type filtering, search, pagination), Resource details
    - Dynamic counts aligned with type facets

---

## SPARQL — endpoint and examples

Fuseki endpoint: `http://localhost:3030/kg-tolkiengateway/sparql`

1) Count total entities (with `schema:name` and `schema.org`/`kg-ont` types)
```sparql
PREFIX schema: <http://schema.org/>
SELECT (COUNT(DISTINCT ?s) AS ?count)
WHERE {
    ?s a ?t ; schema:name ?n .
    FILTER(STRSTARTS(STR(?t), "http://schema.org/") || STRSTARTS(STR(?t), "http://tolkien-kg.org/ontology/"))
}
```

2) Type facets (same filters as UI)
```sparql
PREFIX schema: <http://schema.org/>
SELECT ?t (COUNT(DISTINCT ?s) AS ?count)
WHERE {
    ?s a ?t ; schema:name ?n .
    FILTER(STRSTARTS(STR(?t), "http://schema.org/") || STRSTARTS(STR(?t), "http://tolkien-kg.org/ontology/"))
}
GROUP BY ?t
ORDER BY DESC(?count)
```

3) Implicit types via hierarchy (property paths)
```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?type
WHERE {
    <http://tolkien-kg.org/resource/Elrond> a/rdfs:subClassOf* ?type .
}
```

4) Relationships with `owl:sameAs` propagation
```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?p ?o
WHERE {
    VALUES ?x { <http://tolkien-kg.org/resource/Elrond> }
    {
        ?x (owl:sameAs|^owl:sameAs)? ?x1 .
        ?x1 ?p ?o .
    } UNION {
        ?s ?p ?x1 .
        ?x (owl:sameAs|^owl:sameAs)? ?x1 .
        BIND(?s AS ?o)
    }
}
LIMIT 200
```

---

## Linked Data Interface (navigation)

Main pages:
- Home: type tiles (with icons), global stats
- Browse: filterable entity list by type, search, pagination
- Entity details: summary, image if available, properties (clickable IRIs), timeline when present

Content negotiation:
- HTML by default, Turtle if `Accept: text/turtle`

---

## Design Choices

- Priority reuse of `schema.org` (e.g., `schema:Person`, `schema:CreativeWork`), complemented by `kg-ont` for Tolkien-specific elements
- Prefix normalization (`schema:` everywhere) to avoid ambiguity (`schema1:`)
- Entities normalized as `kg-res:` (alphanumeric, `_`) from titles
- Counts/Stats aligned with facets (UI/SPARQL consistency)

---

## Verification & Quality

- SHACL: `python scripts/rdf/validate_final.py`
- Ontology vs data: `python scripts/rdf/validate_with_ontology.py`
- Control queries (examples above) on Fuseki

---

## Troubleshooting

- Fuseki unavailable: check `http://localhost:3030/` and restart `fuseki-server --mem /kg-tolkiengateway`
- `schema1:` prefix in TTL: scripts automatically correct during serialization/merge
- Inconsistent counters/facets: reload `kg_full.ttl` into Fuseki, then refresh UI

---

## Deliverables

- Reproducible code + scripts
- Final KG: `data/rdf/kg_full.ttl`
- Report/README (this file) documenting choices, pipeline and usage

---

## Key File References

- RDF generation: [scripts/rdf/rdf_maker.py](scripts/rdf/rdf_maker.py)
- Final merge: [scripts/rdf/merge_all_ttl.py](scripts/rdf/merge_all_ttl.py)
- External data: [scripts/rdf/integrate_external_data.py](scripts/rdf/integrate_external_data.py)
- SHACL validation: [scripts/rdf/validate_final.py](scripts/rdf/validate_final.py)
- Ontology: [data/rdf/tolkien-kg-ontology.ttl](data/rdf/tolkien-kg-ontology.ttl)
- Web UI: `web/` (FastAPI)

---

## URLs

- **Home**: http://localhost:8000
- **Browse**: http://localhost:8000/browse
- **API Docs**: http://localhost:8000/docs

---

## Project Structure

```
Semantic-Web-project/
├── api/                    ← FastAPI + Renderers
├── ingestion/              ← Data extraction scripts
├── rdf/
│   ├── RdfData/              ← Ontologies, shapes, TTL
│   └── scripts/              ← Generation, validation, merge
├── data/                   ← Raw data (infoboxes)
├── setup/                  ← Launch scripts
├── docs/                   ← Documentation
├── tests/                  ← Unit tests
├── config.py                  ← Centralized configuration
├── PROJECT_STRUCTURE.md       ← Complete structure guide
├── RDF_SCRIPTS_GUIDE.md       ← Scripts execution guide
├── REFACTORING_SUMMARY.md     ← Change summary
└── requirements.txt           ← Python dependencies
```

**For more details**: See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## Important Scripts

### Data Pipeline

```bash
# 1. Extract infoboxes
python rdf/scripts/rdf_maker.py

# 2. Add multilingual labels
python rdf/scripts/integrate_multilang_labels.py

# 3. Integrate external data
python rdf/scripts/integrate_external_data.py

# 4. Merge all TTL files
python rdf/scripts/merge_all_ttl.py

# 5. Validate with SHACL
python rdf/scripts/validate_final.py
```

### Other Scripts

```bash
# Analyze infobox structure
python rdf/scripts/analyze_infobox_structure.py

# Clean junk properties
python rdf/scripts/cleanup_junk.py

# Compare old vs new data
python rdf/scripts/compare_infoboxes.py
```

**Important**: Execute scripts from **PROJECT ROOT**, not from the script folder.

---

## API Endpoints

### Resources (Linked Data)

```
GET /resource/{name}                    → RDF Turtle by default
GET /resource/{name}?format=html        → HTML
GET /resource/{name}?format=json        → JSON-LD

GET /page/{name}                        → Always HTML
GET /browse                             → Browse interface
GET /                                   → Home page
```

### SPARQL

```
GET /sparql?query=...                   → SPARQL query
POST http://localhost:3030/kg-tolkiengateway/sparql
```

### Documentation

```
GET /docs                               → Swagger UI
GET /redoc                              → ReDoc
```

---

## Data Format

### RDF Namespaces

- `kg-ont:` - Canonical ontology
- `kg-inf:` - Infobox properties
- `kg-res:` - Resources/entities
- `kg-card:` - Cards (TCG game)
- `schema:` - Schema.org
- `dbp:` - DBpedia

### Example Resource

```turtle
kg-res:Aragorn a kg-ont:Character ;
    schema:name "Aragorn"@en ;
    kg-ont:birthDate "TA 2931" ;
    kg-ont:birthLocation kg-res:Rivendell ;
    kg-ont:role "Ranger" ;
    kg-inf:written "Tolkien" ;
    rdfs:label "Aragorn"@en, "Aragorn"@de, "Aragorn"@fr .
```

---

## SHACL Validation

The project uses **SHACL** (Shapes Constraint Language) to validate data integrity:

```bash
# Validate data
python rdf/scripts/validate_final.py

# Expected result: 100% conformance
```

**Applied shapes**:
- 5 NodeShapes (Character, Location, Work, Organization, Artifact)
- 0 violations
- Realistic constraints (INFO/WARNING only)

---

## Documentation

| File | Content |
|---------|---------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Complete structure guide |
| [RDF_SCRIPTS_GUIDE.md](RDF_SCRIPTS_GUIDE.md) | RDF scripts execution guide |
| [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) | Change summary |
| [docs/](docs/) | Detailed documentation (guides, slides, QA) |

---

## Technologies Used

- **Python 3.10+**
- **FastAPI** - Web framework
- **RDFlib** - RDF/TTL manipulation
- **SPARQLWrapper** - SPARQL queries
- **pyshacl** - SHACL validation
- **Apache Jena Fuseki** - Triplestore
- **uvicorn** - ASGI server

---

## Dependency Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Data Flow

```
Tolkien Gateway Wiki
    ↓
infobox_parser.py + wiki_api.py    (ingestion/)
    ↓
rdf_maker.py                        (rdf/scripts/)
    ↓
all_infoboxes.ttl (49,249 triples)
    ↓
[integrate_multilang_labels.py + merge_multilang_labels.py]
    ↓
all_infoboxes_with_lang.ttl
    ↓
[integrate_external_data.py]
    ↓
external_links.ttl
    ↓
[merge_all_ttl.py]
    ↓
kg_full.ttl
    ↓
Upload to Fuseki @ localhost:3030
    ↓
[API Routes via api/main.py]
    ↓
Web Interface (api/)
```

---

## KG Statistics

- **49,249 triples** (100% validated)
- **800+ entities** extracted
- **11 entity types** (Character, Location, Work, etc.)
- **0 ontology redundancies**
- **0 junk properties**
- **100% SHACL conformance**

---

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Extraction** | Active | Operational ingestion scripts |
| **RDF** | Validated | 49,249 triples, 100% SHACL |
| **API** | Production | FastAPI in development mode |
| **Interface** | Complete | Navigation and search |
| **Fuseki** | External | Launch before API |
| **Tests** | To develop | Structure created, tests to write |

---

## Contributing

To contribute:

1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## Support

- See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for structure
- See [RDF_SCRIPTS_GUIDE.md](RDF_SCRIPTS_GUIDE.md) to run scripts
- See [docs/](docs/) for detailed documentation

---

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for more details.

---

## Authors

**Your Team** - Semantic Web Project - January 2026

---

## Educational Objectives

This project demonstrates:
- Structured data extraction from wikis
- Transformation to RDF/OWL
- Semantic ontology design
- SHACL validation
- SPARQL endpoint
- REST API with content negotiation
- Interactive web interface

---

**Last updated**: January 2026  
**Version**: 1.0.0

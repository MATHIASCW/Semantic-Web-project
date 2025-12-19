import time
from rdflib import Graph
import os
import requests
from request import (
    get_all_page_titles,
    get_all_page_titles_page,
    get_titles_with_infobox,
    get_pages_using_template,
    get_infobox_templates_cached,
    get_infobox_wikitext,
    extract_infobox,
    get_page_links,
)
from rdf_builder import infobox_to_rdf, base_entity_graph, add_links_to_graph

SAMPLE_SIZE = 100
FORCE_TITLES = []
FILTER_INFOBOX = True
PAGE_SIZE = 50
TEMPLATE_TITLES = [
    "Template:Infobox_character",
    "Template:Infobox_place",
    "Template:Infobox_event",
]

CATEGORY_TITLE = "Category:Infobox_templates"
TEMPLATES_CACHE = "templates_cache.json"
REFRESH_TEMPLATES = False
USE_AUTO_TEMPLATES = True
USE_SCAN_FALLBACK = False
UPLOAD_TO_FUSEKI = os.getenv("UPLOAD_TO_FUSEKI", "0") == "1"
FUSEKI_DATASET = os.getenv("FUSEKI_DATASET", "kg-tolkiengateway")
FUSEKI_ENDPOINT = os.getenv(
    "FUSEKI_ENDPOINT",
    f"http://localhost:3030/{FUSEKI_DATASET}/data",
)
ADD_LINKS = True
LINK_LIMIT = 200

def collect_titles_from_templates(templates, target):
    collected = []
    seen = set()
    remaining = target
    for tmpl in templates:
        if remaining <= 0:
            break
        batch = get_pages_using_template(tmpl, min(remaining, 200))
        for t in batch:
            if t in seen:
                continue
            seen.add(t)
            collected.append(t)
            remaining -= 1
            if remaining <= 0:
                break
    return collected

def is_real_infobox_template(title):
    return title.lower().startswith("template:infobox ")

if FORCE_TITLES:
    titles = FORCE_TITLES
    total = len(titles)
else:
    if USE_AUTO_TEMPLATES:
        templates = get_infobox_templates_cached(
            CATEGORY_TITLE,
            TEMPLATES_CACHE,
            refresh=REFRESH_TEMPLATES,
        )
        templates = [t for t in templates if is_real_infobox_template(t)]
        titles = collect_titles_from_templates(templates, SAMPLE_SIZE)
        if not titles:
            print("No titles collected from templates; check category/cache.", flush=True)
    elif TEMPLATE_TITLES:
        titles = collect_titles_from_templates(TEMPLATE_TITLES, SAMPLE_SIZE)
    else:
        titles = get_titles_with_infobox(limit=SAMPLE_SIZE) if FILTER_INFOBOX else get_all_page_titles(limit=SAMPLE_SIZE)
    total = len(titles)

kg = Graph()

started = time.time()
found_wikitext = 0
found_infobox = 0
added_graphs = 0

print(f"Start: titles={total} sample_size={SAMPLE_SIZE}", flush=True)

if FORCE_TITLES or not FILTER_INFOBOX or titles:
    for idx, title in enumerate(titles, 1):
        print(f"[{idx}/{total}] {title}", flush=True)

        wikitext = get_infobox_wikitext(title)
        if not wikitext:
            print(f"[{idx}/{total}] no wikitext", flush=True)
            base_graph = base_entity_graph(title)
            if ADD_LINKS:
                links = get_page_links(title, limit=LINK_LIMIT)
                add_links_to_graph(base_graph, title, links)
            kg += base_graph
            continue
        found_wikitext += 1

        infobox = extract_infobox(wikitext)
        if not infobox:
            print(f"[{idx}/{total}] no infobox", flush=True)
            base_graph = base_entity_graph(title)
            if ADD_LINKS:
                links = get_page_links(title, limit=LINK_LIMIT)
                add_links_to_graph(base_graph, title, links)
            kg += base_graph
            continue
        found_infobox += 1

        base_graph = base_entity_graph(title)
        page_graph = infobox_to_rdf(title, infobox)
        if ADD_LINKS:
            links = get_page_links(title, limit=LINK_LIMIT)
            add_links_to_graph(page_graph, title, links)
        kg += base_graph
        kg += page_graph
        added_graphs += 1
        print(f"[{idx}/{total}] graph added", flush=True)

        if idx % 10 == 0:
            elapsed = time.time() - started
            print(
                f"Progress: {idx}/{total} | wikitext: {found_wikitext} | "
                f"infobox: {found_infobox} | graphs: {added_graphs} | "
                f"elapsed: {elapsed:.1f}s",
                flush=True,
            )

        time.sleep(0.5)
elif USE_SCAN_FALLBACK:
    cont = None
    scanned = 0
    target = SAMPLE_SIZE
    while found_infobox < target:
        batch, cont = get_all_page_titles_page(limit=PAGE_SIZE, cont=cont)
        if not batch:
            break
        for title in batch:
            scanned += 1
            print(f"[scan {scanned}] {title}", flush=True)

            wikitext = get_infobox_wikitext(title)
            if not wikitext:
                print(f"[scan {scanned}] no wikitext", flush=True)
                continue
            found_wikitext += 1

            infobox = extract_infobox(wikitext)
            if not infobox:
                print(f"[scan {scanned}] no infobox", flush=True)
                continue
            found_infobox += 1

            page_graph = infobox_to_rdf(title, infobox)
            kg += page_graph
            added_graphs += 1
            print(f"[{found_infobox}/{target}] graph added", flush=True)

            if found_infobox >= target:
                break

            if scanned % 10 == 0:
                elapsed = time.time() - started
                print(
                    f"Progress: scan={scanned} | wikitext: {found_wikitext} | "
                    f"infobox: {found_infobox} | graphs: {added_graphs} | "
                    f"elapsed: {elapsed:.1f}s",
                    flush=True,
                )

            time.sleep(0.5)

        if not cont:
            break

ttl_bytes = kg.serialize(format="turtle", encoding="utf-8")
with open("kg_sample.ttl", "wb") as f:
    f.write(ttl_bytes)
elapsed = time.time() - started
print(
    f"KG sample genere : kg_sample.ttl | total: {total} | "
    f"wikitext: {found_wikitext} | infobox: {found_infobox} | "
    f"graphs: {added_graphs} | elapsed: {elapsed:.1f}s",
    flush=True,
)

try:
    check = Graph()
    check.parse("kg_sample.ttl", format="turtle")
    print(f"TTL valide. Triples: {len(check)}", flush=True)
except Exception as exc:
    print(f"TTL invalide: {exc}", flush=True)

if UPLOAD_TO_FUSEKI:
    try:
        resp = requests.post(
            FUSEKI_ENDPOINT,
            data=ttl_bytes,
            headers={"Content-Type": "text/turtle"},
            timeout=30,
        )
        if resp.status_code >= 200 and resp.status_code < 300:
            print(f"Upload Fuseki OK: {FUSEKI_ENDPOINT}", flush=True)
        else:
            print(
                f"Upload Fuseki KO {resp.status_code}: {resp.text[:200]}",
                flush=True,
            )
    except requests.RequestException as exc:
        print(f"Upload Fuseki error: {exc}", flush=True)

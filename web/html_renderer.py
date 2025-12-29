"""
HTML page rendering and content formatting.
"""
from html import escape
from urllib.parse import quote
import re
from typing import List, Dict, Optional

from .models import ResourceData, TimelineEvent, PageContent


def format_property_label(predicate_uri: str) -> str:
    """Formate un URI de propriété en label lisible"""
    if '#' in predicate_uri:
        label = predicate_uri.split('#')[-1]
    elif '/' in predicate_uri:
        label = predicate_uri.split('/')[-1]
    else:
        label = predicate_uri
    
    label = re.sub(r'([a-z])([A-Z])', r'\1 \2', label)
    return label.title()


def clean_image(value: str) -> str:
    """Nettoie les valeurs d'image issues de TolkienGateway (prefixes Image:/File:)."""
    cleaned = value.strip()
    if cleaned.lower().startswith('image:'):
        cleaned = cleaned[len('Image:'):].strip()
    if cleaned.lower().startswith('file:'):
        cleaned = cleaned[len('File:'):].strip()
    return cleaned


def parse_timeline(template_text: str) -> List[TimelineEvent]:
    """Parse a TolkienGateway Timeline template into periods.
    Returns a list of TimelineEvent objects.
    """
    if not template_text or "{{Timeline" not in template_text:
        return []

    fields = {}
    for key, val in re.findall(r"(\w+)\s*=\s*([^|}]+)", template_text):
        fields[key] = val.strip()

    periods = []
    for sec in range(1, 8):
        era = fields.get(f"section{sec}short") or fields.get(f"section{sec}")
        for p in range(1, 6):
            start = fields.get(f"section{sec}period{p}start")
            end = fields.get(f"section{sec}period{p}end")
            label = fields.get(f"section{sec}period{p}") or fields.get(f"section{sec}period{p}label") or ""
            color = fields.get(f"section{sec}period{p}color") or ""
            if start and end:
                periods.append(TimelineEvent(
                    label=label or "Period",
                    start=start,
                    end=end,
                    color=color,
                    era=era or ""
                ))
    return periods


def extract_timeline_from_properties(properties: Dict[str, List[str]]) -> Optional[str]:
    """Extract timeline template text from properties if present."""
    for _p, _vals in properties.items():
        for _v in _vals:
            if isinstance(_v, str) and '{{Timeline' in _v:
                return _v
    return None


def build_summary_table(resource: ResourceData) -> str:
    """Build DBpedia-style summary table HTML."""
    props_map = resource.properties
    
    def vals(key):
        return props_map.get(key, [])
    
    def render_val(v: str):
        if v.startswith('http://') or v.startswith('https://'):
            lbl = format_property_label(v)
            local = v.rsplit('/', 1)[-1]
            return f'<a href="/resource/{quote(local)}">{escape(lbl)}</a>'
        return escape(v)
    
    summary_rows = []
    
    def add_row(label, key):
        v = vals(key)
        if v:
            summary_rows.append(
                f'<tr><td><strong>{escape(label)}</strong></td><td>{render_val(v[0])}</td></tr>'
            )
    
    add_row('Race', 'http://tolkien-kg.org/ontology/race')
    add_row('Sexe', 'http://tolkien-kg.org/ontology/gender')
    add_row('Naissance', 'http://tolkien-kg.org/ontology/birthDate')
    add_row('Décès', 'http://tolkien-kg.org/ontology/deathDate')
    add_row('Lieu de naissance', 'http://tolkien-kg.org/ontology/birthLocation')
    add_row('Lieu de décès', 'http://tolkien-kg.org/ontology/deathLocation')
    add_row('Maison/Famille', 'http://tolkien-kg.org/ontology/family')
    add_row('Affiliation', 'http://tolkien-kg.org/ontology/affiliation')
    add_row('Époux·se', 'http://tolkien-kg.org/ontology/spouse')
    
    if summary_rows:
        return '<div class="section"><h2>Résumé</h2><table class="timeline-table">' + ''.join(summary_rows) + '</table></div>'
    return ""


def build_properties_section(resource: ResourceData) -> str:
    """Build properties section HTML (all properties list, excluding special fields)."""
    EXCLUDED_PROPERTIES = {
        'http://schema.org/image',
        'http://tolkien-kg.org/ontology/timeline',
        'http://tolkien-kg.org/ontology/additionalcredits',
    }
    
    html = '<div class="properties"><h2>Propriétés</h2>'
    
    for predicate, values in sorted(resource.properties.items()):
        if predicate in EXCLUDED_PROPERTIES:
            continue
        
        prop_label = format_property_label(predicate)
        html += f'<div class="property">'
        html += f'<div class="property-name">{escape(prop_label)}</div>'
        html += '<div class="property-value">'
        
        for value in values:
            if isinstance(value, str) and '{{Timeline' in value:
                continue
            
            if value.startswith('http://') or value.startswith('https://'):
                value_label = format_property_label(value)
                local = value.rsplit('/', 1)[-1]
                html += f'<div class="value-item"><a href="/resource/{quote(local)}">{escape(value_label)}</a></div>'
            else:
                html += f'<div class="value-item">{escape(str(value))}</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html


def build_timeline_section(events: List[TimelineEvent]) -> str:
    """Build timeline/chronology section HTML."""
    if not events:
        return ""
    
    html = '<div class="section">'
    html += '<h3>Chronologie</h3>'
    html += '<table class="timeline-table">'
    html += '<thead><tr><th>Période</th><th>Ère</th><th>Début</th><th>Fin</th></tr></thead><tbody>'
    
    for event in events:
        html += f'<tr><td>{escape(event.label)}</td><td>{escape(event.era)}</td><td>{escape(event.start)}</td><td>{escape(event.end)}</td></tr>'
    
    html += '</tbody></table></div>'
    return html


def build_image_section(image_url: Optional[str], resource_name: str) -> str:
    """Build image display section HTML."""
    if not image_url:
        return ""
    
    if image_url.startswith('http'):
        return f'<img src="{escape(image_url)}" alt="{escape(resource_name)}" class="thumbnail" onerror="this.style.display=\'none\';">'
    else:
        file_name = clean_image(image_url)
        file_page = f"https://tolkiengateway.net/wiki/File:{file_name}"
        return f'<div><strong>Image:</strong> <a href="{escape(file_page)}" target="_blank">{escape(file_name)}</a></div>'


def get_css_styles() -> str:
    """Return CSS styles for HTML pages (DBpedia-like style)."""
    return """
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background: #f5f5f5; 
                color: #333;
            }
            .container { 
                max-width: 1200px; 
                margin: 30px auto; 
                padding: 0 20px;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            /* Header section */
            .page-header {
                border-bottom: 1px solid #e5e5e5;
                padding: 30px 0;
                margin-bottom: 30px;
            }
            .page-title {
                font-size: 28px;
                font-weight: bold;
                color: #1a472a;
                margin-bottom: 5px;
            }
            .page-subtitle {
                font-size: 14px;
                color: #666;
                line-height: 1.6;
            }
            .page-subtitle a {
                color: #0066cc;
                text-decoration: none;
            }
            .page-subtitle a:hover {
                text-decoration: underline;
            }
            
            /* Image section */
            .infobox {
                float: right;
                width: 300px;
                margin-left: 20px;
                margin-bottom: 20px;
                text-align: center;
            }
            .infobox img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            /* Properties table */
            .properties-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                clear: both;
            }
            .properties-table tr {
                border-bottom: 1px solid #e5e5e5;
            }
            .properties-table tr:hover {
                background: #f9f9f9;
            }
            .properties-table th {
                background: #f5f5f5;
                text-align: left;
                font-weight: 600;
                padding: 12px 15px;
                border-bottom: 2px solid #ddd;
            }
            .properties-table td {
                padding: 12px 15px;
                vertical-align: top;
            }
            .property-name {
                font-weight: 600;
                color: #0066cc;
                width: 30%;
                word-break: break-word;
            }
            .property-name a {
                color: #0066cc;
                text-decoration: none;
            }
            .property-name a:hover {
                text-decoration: underline;
            }
            .property-value {
                width: 70%;
            }
            .property-value a {
                color: #0066cc;
                text-decoration: none;
            }
            .property-value a:hover {
                text-decoration: underline;
            }
            .value-list {
                list-style: none;
            }
            .value-list li {
                margin: 3px 0;
            }
            .value-list li:before {
                content: "• ";
                margin-right: 5px;
            }
            
            /* Timeline section */
            .timeline-section {
                margin-top: 40px;
                padding-top: 30px;
                border-top: 1px solid #e5e5e5;
                clear: both;
            }
            .timeline-section h2 {
                color: #1a472a;
                font-size: 18px;
                margin-bottom: 15px;
                border-bottom: 2px solid #1a472a;
                padding-bottom: 10px;
            }
            .timeline-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .timeline-table th {
                background: #f5f5f5;
                text-align: left;
                font-weight: 600;
                padding: 10px 12px;
                border-bottom: 2px solid #ddd;
            }
            .timeline-table td {
                padding: 8px 12px;
                border-bottom: 1px solid #e5e5e5;
            }
            .timeline-table tr:hover {
                background: #f9f9f9;
            }
            
            /* Linked data section */
            .linked-data {
                margin-top: 30px;
                padding: 15px;
                background: #f0f8ff;
                border: 1px solid #b3d9ff;
                border-radius: 4px;
                clear: both;
            }
            .linked-data h3 {
                color: #1a472a;
                margin-bottom: 10px;
                font-size: 16px;
            }
            .format-links a {
                display: inline-block;
                margin-right: 15px;
                padding: 6px 12px;
                background: #0066cc;
                color: white;
                text-decoration: none;
                border-radius: 3px;
                font-size: 14px;
            }
            .format-links a:hover {
                background: #0052a3;
            }
            
            /* Footer */
            .page-footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e5e5;
                text-align: center;
                font-size: 13px;
                color: #666;
            }
            .page-footer a {
                color: #0066cc;
                text-decoration: none;
                margin: 0 10px;
            }
            .page-footer a:hover {
                text-decoration: underline;
            }
    """


def generate_html_page(resource: ResourceData) -> str:
    """Generate complete HTML page for a resource (DBpedia-style)."""
    if not resource:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Not Found</title></head>
        <body>
            <h1>Ressource non trouvée</h1>
            <p>Ressource non disponible</p>
            <a href="/">Retour</a>
        </body>
        </html>
        """
    
    image_url = resource.get_first_value('http://schema.org/image')
    timeline_text = resource.get_first_value('http://tolkien-kg.org/ontology/timeline')
    timeline_events = parse_timeline(timeline_text) if timeline_text else []
    
    resource_type = "Ressource"
    rdf_type = resource.get_first_value('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
    if rdf_type:
        resource_type = format_property_label(rdf_type)
    
    image_html = ""
    if image_url:
        if image_url.startswith('http'):
            image_html = f'<div class="infobox"><img src="{escape(image_url)}" alt="{escape(resource.name)}" onerror="this.style.display=\'none\';"></div>'
        else:
            file_name = clean_image(image_url)
            file_page = f"https://tolkiengateway.net/wiki/File:{file_name}"
            image_html = f'<div class="infobox"><p><strong>Image:</strong> <a href="{escape(file_page)}" target="_blank">{escape(file_name)}</a></p></div>'
    
    EXCLUDED_PROPERTIES = {
        'http://schema.org/image',
        'http://tolkien-kg.org/ontology/timeline',
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    }
    
    properties_rows = []
    for predicate, values in sorted(resource.properties.items()):
        if predicate in EXCLUDED_PROPERTIES:
            continue
        
        prop_label = format_property_label(predicate)
        prop_link = f'<a href="{escape(predicate)}" title="{escape(predicate)}">{escape(prop_label)}</a>'
        
        value_parts = []
        for value in values:
            if value.startswith('http://') or value.startswith('https://'):
                value_label = format_property_label(value)
                local = value.rsplit('/', 1)[-1]
                value_parts.append(f'<a href="/resource/{quote(local)}">{escape(value_label)}</a>')
            else:
                value_parts.append(f'<span>{escape(str(value))}</span>')
        
        value_html = '<br>'.join(value_parts) if value_parts else "-"
        properties_rows.append(f'<tr><td class="property-name">{prop_link}</td><td class="property-value">{value_html}</td></tr>')
    
    properties_table = '<table class="properties-table"><thead><tr><th>Propriété</th><th>Valeur</th></tr></thead><tbody>' + ''.join(properties_rows) + '</tbody></table>'
    
    timeline_html = ""
    if timeline_events:
        timeline_rows = []
        for event in timeline_events:
            timeline_rows.append(f'<tr><td>{escape(event.label)}</td><td>{escape(event.era)}</td><td>{escape(event.start)}</td><td>{escape(event.end)}</td></tr>')
        timeline_html = f'''
        <div class="timeline-section">
            <h2>Chronologie</h2>
            <table class="timeline-table">
                <thead><tr><th>Période</th><th>Ère</th><th>Début</th><th>Fin</th></tr></thead>
                <tbody>{"".join(timeline_rows)}</tbody>
            </table>
        </div>
        '''
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(resource.name)} - Tolkien Knowledge Graph</title>
        <style>
            {get_css_styles()}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="page-header">
                <h1 class="page-title">About: {escape(resource.name)}</h1>
                <div class="page-subtitle">
                    An Entity of Type: <strong>{resource_type}</strong>, 
                    from Knowledge Graph: <a href="http://tolkien-kg.org" target="_blank">tolkien-kg.org</a>
                </div>
            </div>
            
            {image_html}
            
            {properties_table}
            
            {timeline_html}
            
            <div class="linked-data">
                <h3>Formats disponibles</h3>
                <div class="format-links">
                    <a href="/resource/{quote(resource.uri.rsplit('/', 1)[-1])}?format=turtle">📄 Turtle (RDF)</a>
                    <a href="/resource/{quote(resource.uri.rsplit('/', 1)[-1])}?format=json">📋 JSON</a>
                    <a href="/resource/{quote(resource.uri.rsplit('/', 1)[-1])}">🌐 HTML</a>
                </div>
            </div>
            
            <div class="page-footer">
                <a href="/">← Accueil</a> | 
                <a href="/characters">Personnages</a> |
                <strong>URI:</strong> <code>{escape(resource.uri)}</code>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_turtle_for_resource(resource: ResourceData) -> str:
    """Generate Turtle/RDF representation of a resource."""
    turtle = f"""@prefix kg-ont: <http://tolkien-kg.org/ontology/> .
@prefix kg-res: <http://tolkien-kg.org/resource/> .
@prefix schema: <http://schema.org/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dbp: <http://dbpedia.org/property/> .

<{resource.uri}> """
    
    first = True
    for predicate, values in sorted(resource.properties.items()):
        if not first:
            turtle += " ;\n    "
        first = False
        
        if predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
            turtle += "a "
        else:
            turtle += f"<{predicate}> "
        
        value_strings = []
        for value in values:
            if value.startswith('http://') or value.startswith('https://'):
                value_strings.append(f"<{value}>")
            else:
                escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                value_strings.append(f'"{escaped}"')
        
        turtle += ", ".join(value_strings)
    
    turtle += " .\n"
    return turtle

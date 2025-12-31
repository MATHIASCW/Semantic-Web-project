"""
HTML page rendering and content formatting.
"""
from html import escape
from urllib.parse import quote
import re
from typing import List, Dict, Optional

from .models import ResourceData, TimelineEvent, PageContent
from .styles import get_resource_css


def format_property_label(predicate_uri: str) -> str:
    """Format a property URI into a human-readable label."""
    if '#' in predicate_uri:
        label = predicate_uri.split('#')[-1]
    elif '/' in predicate_uri:
        label = predicate_uri.split('/')[-1]
    else:
        label = predicate_uri
    
    label = re.sub(r'([a-z])([A-Z])', r'\1 \2', label)
    return label.title()


def clean_image(value: str) -> str:
    """Clean TolkienGateway image values (Image:/File: prefixes)."""
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
    add_row('Gender', 'http://tolkien-kg.org/ontology/gender')
    add_row('Birth', 'http://tolkien-kg.org/ontology/birthDate')
    add_row('Death', 'http://tolkien-kg.org/ontology/deathDate')
    add_row('Birth location', 'http://tolkien-kg.org/ontology/birthLocation')
    add_row('Death location', 'http://tolkien-kg.org/ontology/deathLocation')
    add_row('House/Family', 'http://tolkien-kg.org/ontology/family')
    add_row('Affiliation', 'http://tolkien-kg.org/ontology/affiliation')
    add_row('Spouse', 'http://tolkien-kg.org/ontology/spouse')
    
    if summary_rows:
        return '<div class="section"><h2>Summary</h2><table class="timeline-table">' + ''.join(summary_rows) + '</table></div>'
    return ""


def build_properties_section(resource: ResourceData) -> str:
    """Build properties section HTML (all properties list, excluding special fields)."""
    EXCLUDED_PROPERTIES = {
        'http://schema.org/image',
        'http://tolkien-kg.org/ontology/timeline',
        'http://tolkien-kg.org/ontology/additionalcredits',
    }
    
    html = '<div class="properties"><h2>Properties</h2>'
    
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
    html += '<h3>Timeline</h3>'
    html += '<table class="timeline-table">'
    html += '<thead><tr><th>Period</th><th>Era</th><th>Start</th><th>End</th></tr></thead><tbody>'
    
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




def generate_html_page(resource: ResourceData) -> str:
    """Generate complete HTML page for a resource (DBpedia-style)."""
    if not resource:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>Not Found</title></head>
        <body>
            <h1>Resource not found</h1>
            <p>Resource not available</p>
            <a href="/">Home</a>
        </body>
        </html>
        """
    
    image_url = resource.get_first_value('http://schema.org/image')
    timeline_text = resource.get_first_value('http://tolkien-kg.org/ontology/timeline')
    timeline_events = parse_timeline(timeline_text) if timeline_text else []
    
    resource_type = "Resource"
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
    
    properties_table = '<table class="properties-table"><thead><tr><th>Property</th><th>Value</th></tr></thead><tbody>' + ''.join(properties_rows) + '</tbody></table>'
    
    timeline_html = ""
    if timeline_events:
        timeline_rows = []
        for event in timeline_events:
            timeline_rows.append(f'<tr><td>{escape(event.label)}</td><td>{escape(event.era)}</td><td>{escape(event.start)}</td><td>{escape(event.end)}</td></tr>')
        timeline_html = f'''
        <div class="timeline-section">
            <h2>Timeline</h2>
            <table class="timeline-table">
                <thead><tr><th>Period</th><th>Era</th><th>Start</th><th>End</th></tr></thead>
                <tbody>{"".join(timeline_rows)}</tbody>
            </table>
        </div>
        '''
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(resource.name)} - Tolkien Knowledge Graph</title>
        <style>
            {get_resource_css()}
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
                <h3>Available formats</h3>
                <div class="format-links">
                    <a href="/resource/{quote(resource.uri.rsplit('/', 1)[-1])}?format=turtle">📄 Turtle (RDF)</a>
                    <a href="/resource/{quote(resource.uri.rsplit('/', 1)[-1])}?format=json">📋 JSON</a>
                    <a href="/resource/{quote(resource.uri.rsplit('/', 1)[-1])}">🌐 HTML</a>
                </div>
            </div>
            
            <div class="page-footer">
                <a href="/">← Home</a> | 
                <a href="/browse?type=Character">Characters</a> |
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

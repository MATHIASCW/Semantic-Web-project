"""
Analysis of Tolkien Gateway infobox structure

This script scans all infobox_*.txt files and analyzes:
- Template types used ({{Infobox character}}, {{Album}}, etc.)
- Fields (parameters) of each template
- Fields COMMON vs SPECIFIC to each type
- Coverage of the property_map from rdf_maker.py
- Unmapped fields (which could cause issues in RDF)

Result: detailed HTML report + CSV files
"""

import os
import re
import json
from collections import defaultdict
from pathlib import Path
import wikitextparser as wtp


def clean_value(v):
    """Minimal cleanup for analysis."""
    v = re.sub(r'<br\s*/?>', ' ', v)
    v = re.sub(r'</?[^>]+>', '', v)
    return v.strip()


def extract_infobox_block(wikitext):
    """Extracts the raw {{Infobox ...}} or {{Type infobox ...}} block."""
    lower = wikitext.lower()
    patterns = [
        r'\{\{\s*infobox',
        r'\{\{\s*\w+\s+infobox',
    ]
    start = -1
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            start = match.start()
            break
    
    if start == -1:
        match = re.search(r'\{\{(\w+)', wikitext)
        if match:
            start = match.start()
        else:
            return None
    
    count = 0
    for i in range(start, len(wikitext)):
        if wikitext[i:i+2] == '{{':
            count += 1
        elif wikitext[i:i+2] == '}}':
            count -= 1
            if count == 0:
                return wikitext[start:i+2]
    return None


def parse_infobox(text):
    """Parse a template via wikitextparser and return (template_name, fields_dict)."""
    parsed = wtp.parse(text)
    
    infobox_tpl = None
    fallback_tpl = None
    
    for t in parsed.templates:
        name = t.name.strip().lower()
        if 'infobox' in name:
            infobox_tpl = t
            break
        if fallback_tpl is None:
            fallback_tpl = t
    
    chosen = infobox_tpl or fallback_tpl
    if not chosen:
        return (None, {})
    
    name = chosen.name.strip().lower()
    fields = {}
    for arg in chosen.arguments:
        key = arg.name.strip()
        value = clean_value(arg.value.strip())
        if value: 
            fields[key] = value
    
    return (name, fields)


def analyze_infoboxes():
    """Scans all data/infoboxes and builds statistics."""
    input_dir = "data/infoboxes"
    
    template_types = defaultdict(list) 
    template_stats = defaultdict(lambda: {
        'count': 0,
        'fields': defaultdict(int),  
        'examples': []
    })
    all_fields = set()
    
    files = [f for f in os.listdir(input_dir) 
             if f.startswith("infobox_") and f.endswith(".txt")]
    
    print(f"Analyzing {len(files)} infobox files...\n")
    
    for filename in sorted(files):
        with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            continue
        
        entity_name = lines[0].replace("---", "").strip()
        infobox_text = "".join(lines[1:])
        
        infobox_block = extract_infobox_block(infobox_text)
        if not infobox_block:
            continue
        
        template_name, fields = parse_infobox(infobox_block)
        if not template_name:
            continue
        
        template_normalized = template_name.replace("infobox ", "").title()
        if not template_normalized.startswith("Infobox"):
            template_normalized = template_normalized
        
        template_stats[template_normalized]['count'] += 1
        if len(template_stats[template_normalized]['examples']) < 2:
            template_stats[template_normalized]['examples'].append(entity_name)
        
        for field in fields.keys():
            template_stats[template_normalized]['fields'][field] += 1
            all_fields.add(field)
    
    return template_stats, all_fields


def load_property_map():
    """Load the property_map from rdf_maker.py."""
    property_map = {
        'name': 'schema:name',
        'birth': 'kg-ont:birthDate',
        'birthlocation': 'kg-ont:birthLocation',
        'birthLocation': 'kg-ont:birthLocation',
        'brithlocation': 'kg-ont:birthLocation',
        'deathlocation': 'kg-ont:deathLocation',
        'deathLocation': 'kg-ont:deathLocation',
        'death': 'kg-ont:deathDate',
        'gender': 'schema:gender',
        'image': 'schema:image',
        'parentage': 'kg-ont:parentage',
        'spouse': 'kg-ont:spouse',
        'children': 'kg-ont:children',
        'titles': 'kg-ont:position',
        'location': 'schema:location',
        'house': 'kg-ont:family',
        'family': 'kg-ont:family',
        'age': 'schema:age',
        'notablefor': 'schema:description',
        'notableFor': 'schema:description',
        'race': 'kg-ont:race',
        'weapons': 'kg-ont:weapons',
        'weapon': 'kg-ont:weapons',
        'steed': 'kg-ont:steed',
        'mount': 'kg-ont:steed',
    }
    return property_map


def generate_report(template_stats, all_fields):
    """Generate a structural analysis report."""
    property_map = load_property_map()
    
    output_file = "infobox_structure_report.html"
    
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Infobox Structure Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; border-bottom: 2px solid #1a472a; padding-bottom: 5px; }
        h3 { color: #888; }
        table { border-collapse: collapse; width: 100%; background: white; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #1a472a; color: white; }
        tr:hover { background: #f9f9f9; }
        .mapped { color: green; }
        .unmapped { color: red; font-weight: bold; }
        .rare { color: orange; }
        .summary { background: #f0f0f0; padding: 10px; margin: 10px 0; border-left: 4px solid #1a472a; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
        .stat-box { background: white; padding: 15px; border-radius: 5px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-box h3 { margin: 0 0 10px 0; }
        .stat-box .number { font-size: 2em; font-weight: bold; color: #1a472a; }
    </style>
</head>
<body>
    <h1>📄 Analysis of Tolkien Gateway Infobox Structure</h1>
""")
        
        total_infoboxes = sum(ts['count'] for ts in template_stats.values())
        unique_templates = len(template_stats)
        unique_fields = len(all_fields)
        mapped_fields = len([f for f in all_fields if f in property_map or f.lower() in property_map])
        unmapped_fields = unique_fields - mapped_fields
        
        out.write(f"""
    <div class="stats">
        <div class="stat-box">
            <h3>Total data/infoboxes</h3>
            <div class="number">{total_infoboxes}</div>
        </div>
        <div class="stat-box">
            <h3>Template Types</h3>
            <div class="number">{unique_templates}</div>
        </div>
        <div class="stat-box">
            <h3>Unique Fields</h3>
            <div class="number">{unique_fields}</div>
        </div>
    </div>
    
    <div class="summary">
        <strong>Property_map coverage:</strong><br>
        ✅ Mapped: <span class="mapped">{mapped_fields}</span> ({100*mapped_fields/unique_fields:.1f}%)<br>
        ❌ Unmapped: <span class="unmapped">{unmapped_fields}</span> ({100*unmapped_fields/unique_fields:.1f}%)
    </div>
""")
        
        out.write("<h2>Details by Template Type</h2>\n")
        out.write("""
    <table>
        <tr>
            <th>Template Type</th>
            <th>Count</th>
            <th>Distinct Fields</th>
            <th>Examples</th>
        </tr>
""")
        
        for template in sorted(template_stats.keys(), key=lambda t: template_stats[t]['count'], reverse=True):
            stats = template_stats[template]
            fields_count = len(stats['fields'])
            examples = ", ".join(stats['examples'][:2])
            
            out.write(f"""        <tr>
            <td><strong>{template}</strong></td>
            <td>{stats['count']}</td>
            <td>{fields_count}</td>
            <td><em>{examples}</em></td>
        </tr>
""")
        
        out.write("    </table>\n")
        
        out.write("<h2>⚠️ Unmapped Fields (Risk)</h2>\n")
        unmapped = sorted([f for f in all_fields if f not in property_map and f.lower() not in property_map],
                         key=lambda f: sum(ts['fields'].get(f, 0) for ts in template_stats.values()),
                         reverse=True)
        
        if unmapped:
            out.write("<table>\n<tr><th>Field</th><th>Total Frequency</th><th>Affected Types</th></tr>\n")
            for field in unmapped[:30]:
                freq = sum(ts['fields'].get(field, 0) for ts in template_stats.values())
                types_with_field = [t for t in template_stats if field in template_stats[t]['fields']]
                out.write(f"""<tr>
                <td class="unmapped">{field}</td>
                <td>{freq}</td>
                <td>{', '.join(types_with_field[:3])}</td>
            </tr>
""")
            out.write("</table>\n")
        else:
            out.write("<p class='mapped'>✅ All fields are mapped!</p>\n")
        
        out.write("<h2>💡 Recommendations</h2>\n")
        out.write("""
    <div class="summary">
        <h3>For rdf_maker.py:</h3>
        <ul>
            <li><strong>Add to property_map:</strong> all frequently appearing unmapped fields</li>
            <li><strong>Use generic fallback:</strong> <code>kg-ont:{field_name}</code> for unknown fields</li>
            <li><strong>Type entities:</strong> based on template used (Character, Book, Film, etc.)</li>
        </ul>
    </div>
    
    <div class="summary">
        <h3>For ontology (tolkien-kg-ontology.ttl):</h3>
        <ul>
            <li>Extend with properties for new types (Film, Book, Song, Album, etc.)</li>
            <li>Add classes: Film, Book, Album, Song, Battle, Organization, Location</li>
            <li>Define appropriate relationships</li>
        </ul>
    </div>
    
    <div class="summary">
        <h3>For SHACL (tolkien-shapes.ttl):</h3>
        <ul>
            <li>Create type-specific shapes (CharacterShape, FilmShape, BookShape, etc.)</li>
            <li>Define required/recommended properties for each type</li>
            <li>Validate only if type is known</li>
        </ul>
    </div>
""")
        
        out.write("</body>\n</html>")
    
    print(f"✅ Report saved: {output_file}")
    
    csv_file = "infobox_fields_mapping.csv"
    with open(csv_file, "w", encoding="utf-8") as csv:
        csv.write("Field,Status,RDF Predicate,Frequency,Examples\n")
        for field in sorted(all_fields):
            is_mapped = field in property_map or field.lower() in property_map
            rdf_pred = property_map.get(field, property_map.get(field.lower(), "❌ MISSING"))
            freq = sum(ts['fields'].get(field, 0) for ts in template_stats.values())
            examples = [t for t in template_stats if field in template_stats[t]['fields']][:2]
            status = "✅ MAPPED" if is_mapped else "❌ UNMAPPED"
            csv.write(f'"{field}",{status},"{rdf_pred}",{freq},"{"; ".join(examples)}"\n')
    
    print(f"✅ CSV generated: {csv_file}\n")


def print_summary(template_stats):
    """Display a summary in console."""
    print("\n" + "="*80)
    print("SUMMARY BY TEMPLATE TYPE")
    print("="*80 + "\n")
    
    for template in sorted(template_stats.keys(), 
                          key=lambda t: template_stats[t]['count'], 
                          reverse=True):
        stats = template_stats[template]
        print(f"📋 {template}")
        print(f"   • Number of data/infoboxes: {stats['count']}")
        print(f"   • Distinct fields: {len(stats['fields'])}")
        print(f"   • Common fields: {', '.join(sorted(list(stats['fields'].keys())[:5]))}...")
        print()


if __name__ == "__main__":
    template_stats, all_fields = analyze_infoboxes()
    print_summary(template_stats)
    generate_report(template_stats, all_fields)



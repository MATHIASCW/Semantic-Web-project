"""
Analyse de la structure des infobox Tolkien Gateway

Ce script scanne tous les fichiers infobox_*.txt et analyse :
- Les types de templates utilisés ({{Infobox character}}, {{Album}}, etc.)
- Les champs (paramètres) de chaque template
- Les champs COMMUNS vs SPÉCIFIQUES à chaque type
- La couverture du property_map du rdf_maker.py
- Les champs non mappés (qui pourraient poser problème en RDF)

Résultat : rapport détaillé en HTML + fichiers CSV
"""

import os
import re
import json
from collections import defaultdict
from pathlib import Path
import wikitextparser as wtp


def clean_value(v):
    """Minimal cleanup pour analyse."""
    v = re.sub(r'<br\s*/?>', ' ', v)
    v = re.sub(r'</?[^>]+>', '', v)
    return v.strip()


def extract_infobox_block(wikitext):
    """Extrait le bloc {{Infobox ...}} brut."""
    start = wikitext.lower().find('{{infobox')
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
    """Parse un template via wikitextparser et retourne (template_name, fields_dict)."""
    parsed = wtp.parse(text)
    for t in parsed.templates:
        name = t.name.strip().lower()
        fields = {}
        for arg in t.arguments:
            key = arg.name.strip()
            value = clean_value(arg.value.strip())
            if value: 
                fields[key] = value
        return (name, fields)
    return (None, {})


def analyze_infoboxes():
    """Scanne tous les infobox et construit des statistiques."""
    input_dir = "infoboxes"
    
    template_types = defaultdict(list) 
    template_stats = defaultdict(lambda: {
        'count': 0,
        'fields': defaultdict(int),  
        'examples': []
    })
    all_fields = set()
    
    files = [f for f in os.listdir(input_dir) 
             if f.startswith("infobox_") and f.endswith(".txt")]
    
    print(f"Analyse de {len(files)} fichiers infobox...\n")
    
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
    """Charge le property_map du rdf_maker.py."""
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
    """Génère un rapport d'analyse structurel."""
    property_map = load_property_map()
    
    output_file = "infobox_structure_report.html"
    
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Analyse Structure Infobox</title>
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
    <h1>📊 Analyse de la Structure des Infobox Tolkien Gateway</h1>
""")
        
        total_infoboxes = sum(ts['count'] for ts in template_stats.values())
        unique_templates = len(template_stats)
        unique_fields = len(all_fields)
        mapped_fields = len([f for f in all_fields if f in property_map or f.lower() in property_map])
        unmapped_fields = unique_fields - mapped_fields
        
        out.write(f"""
    <div class="stats">
        <div class="stat-box">
            <h3>Infobox Total</h3>
            <div class="number">{total_infoboxes}</div>
        </div>
        <div class="stat-box">
            <h3>Types de Template</h3>
            <div class="number">{unique_templates}</div>
        </div>
        <div class="stat-box">
            <h3>Champs Uniques</h3>
            <div class="number">{unique_fields}</div>
        </div>
    </div>
    
    <div class="summary">
        <strong>Couverture du property_map:</strong><br>
        ✅ Mappés: <span class="mapped">{mapped_fields}</span> ({100*mapped_fields/unique_fields:.1f}%)<br>
        ❌ Non-mappés: <span class="unmapped">{unmapped_fields}</span> ({100*unmapped_fields/unique_fields:.1f}%)
    </div>
""")
        
        out.write("<h2>Détail par Type de Template</h2>\n")
        out.write("""
    <table>
        <tr>
            <th>Type de Template</th>
            <th>Nombre</th>
            <th>Champs Distincts</th>
            <th>Exemples</th>
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
        
        out.write("<h2>⚠️ Champs Non-Mappés (Risque)</h2>\n")
        unmapped = sorted([f for f in all_fields if f not in property_map and f.lower() not in property_map],
                         key=lambda f: sum(ts['fields'].get(f, 0) for ts in template_stats.values()),
                         reverse=True)
        
        if unmapped:
            out.write("<table>\n<tr><th>Champ</th><th>Fréquence Totale</th><th>Types Concernés</th></tr>\n")
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
            out.write("<p class='mapped'>✅ Tous les champs sont mappés!</p>\n")
        
        out.write("<h2>💡 Recommandations</h2>\n")
        out.write("""
    <div class="summary">
        <h3>Pour le rdf_maker.py:</h3>
        <ul>
            <li><strong>Ajouter au property_map:</strong> tous les champs non-mappés qui apparaissent fréquemment</li>
            <li><strong>Utiliser un fallback générique:</strong> <code>kg-ont:{field_name}</code> pour les champs inconnus</li>
            <li><strong>Typer les entités:</strong> basé sur le template utilisé (Character, Book, Film, etc.)</li>
        </ul>
    </div>
    
    <div class="summary">
        <h3>Pour l'ontologie (tolkien-kg-ontology.ttl):</h3>
        <ul>
            <li>Étendre avec des propriétés pour les nouveaux types (Film, Book, Song, Album, etc.)</li>
            <li>Ajouter des classes: Film, Book, Album, Song, Battle, Organization, Location</li>
            <li>Définir des relations appropriées</li>
        </ul>
    </div>
    
    <div class="summary">
        <h3>Pour SHACL (tolkien-shapes.ttl):</h3>
        <ul>
            <li>Créer des shapes spécifiques par type (CharacterShape, FilmShape, BookShape, etc.)</li>
            <li>Définir les propriétés obligatoires/recommandées pour chaque type</li>
            <li>Valider uniquement si le type est connu</li>
        </ul>
    </div>
""")
        
        out.write("</body>\n</html>")
    
    print(f"✅ Rapport sauvegardé: {output_file}")
    
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
    
    print(f"✅ CSV généré: {csv_file}\n")


def print_summary(template_stats):
    """Affiche un résumé en console."""
    print("\n" + "="*80)
    print("RÉSUMÉ PAR TYPE DE TEMPLATE")
    print("="*80 + "\n")
    
    for template in sorted(template_stats.keys(), 
                          key=lambda t: template_stats[t]['count'], 
                          reverse=True):
        stats = template_stats[template]
        print(f"📋 {template}")
        print(f"   • Nombre d'infobox: {stats['count']}")
        print(f"   • Champs distincts: {len(stats['fields'])}")
        print(f"   • Champs courants: {', '.join(sorted(list(stats['fields'].keys())[:5]))}...")
        print()


if __name__ == "__main__":
    template_stats, all_fields = analyze_infoboxes()
    print_summary(template_stats)
    generate_report(template_stats, all_fields)

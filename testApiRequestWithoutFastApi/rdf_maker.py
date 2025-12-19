
import os
import re
def wiki_value_to_rdf(value, subj, pred, out):
    link_pattern = re.compile(r'\[\[(.+?)(\|(.+?))?\]\]')
    last_end = 0
    found = False
    for m in link_pattern.finditer(value):
        found = True
        if m.start() > last_end:
            literal = value[last_end:m.start()].strip()
            if literal:
                out.write(f"  ;\n  {pred} \"{literal}\"")
        target = m.group(1).strip().replace(' ', '_')
        label = m.group(3).strip() if m.group(3) else target.replace('_', ' ')
        out.write(f"  ;\n  {pred} ex:{target}")
        if label != target.replace('_', ' '):
            out.write(f" ;\n  rdfs:label \"{label}\"")
        last_end = m.end()
    if found and last_end < len(value):
        literal = value[last_end:].strip()
        if literal:
            out.write(f"  ;\n  {pred} \"{literal}\"")
    return found

input_dir = "infoboxes"
output_dir = "rdf"
os.makedirs(output_dir, exist_ok=True)

def extract_infobox_block(wikitext):
    start = wikitext.lower().find('{{infobox')
    if start == -1:
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
    block = extract_infobox_block(text)
    if not block:
        return {}
    lines = block.splitlines()
    data = {}
    for line in lines[1:]:
        if line.strip().startswith('|'):
            line = line.strip()[1:]
            if '=' in line:
                key, value = line.split('=', 1)
                data[key.strip()] = value.strip()
    return data


property_map = {
    'name': 'schema:name',
    'birth': 'dbp:birthDate',
    'birthlocation': 'schema:birthPlace',
    'gender': 'schema:gender',
    'image': 'schema:image',
    'parentage': 'schema:parent',
    'spouse': 'schema:spouse',
    'children': 'schema:children',
    'titles': 'schema:jobTitle',
    'location': 'schema:location',
    'house': 'dbp:house',
    'age': 'schema:age',
    'notablefor': 'schema:description',
}

output_file = os.path.join(output_dir, "all_infoboxes.ttl")
with open(output_file, "w", encoding="utf-8") as out:
    out.write("""@prefix ex: <http://example.org/> .
@prefix schema: <http://schema.org/> .
@prefix dbp: <http://dbpedia.org/property/> .
@prefix dbr: <http://dbpedia.org/resource/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

""")
    for fname in os.listdir(input_dir):
        if fname.startswith("infobox_") and fname.endswith(".txt"):
            with open(os.path.join(input_dir, fname), encoding="utf-8") as f:
                lines = f.readlines()
            entity = lines[0].replace("---", "").strip()
            infobox_text = "".join(lines[1:])
            data = parse_infobox(infobox_text)
            subj = f"ex:{entity.replace(' ', '_')}"
            out.write(f"{subj} a schema:Person")
            first = True
            for k, v in data.items():
                if v:
                    pred = property_map.get(k.lower(), f"ex:{k.replace(' ', '_')}")
                    # Traite les liens wiki
                    if wiki_value_to_rdf(v, subj, pred, out):
                        first = False
                    else:
                        if not first:
                            out.write("  ;\n")
                        out.write(f"  {pred} \"{v}\"")
                        first = False
            out.write(" .\n\n")
            print(f"RDF triples added for {entity}")
    print(f"All infoboxes written to {output_file}")

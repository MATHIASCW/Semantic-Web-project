import os
import re
import wikitextparser as wtp

"""
Génération de RDF Turtle à partir des infobox

Ce script lit les fichiers infobox_*.txt présents dans le dossier infoboxes/ (produits par requestAllInfobox.py),
analyse les templates {{Infobox ...}} via wikitextparser, normalise les valeurs (suppression HTML/templates, gestion
des liens wiki), mappe les champs vers des prédicats RDF, et écrit un fichier Turtle rdf/all_infoboxes.ttl.

Fonctions clés
- `clean_value(v)`: nettoie HTML simple, références <ref>, entités; convertit templates de dates en texte.
- `ttl_escape(s)`: échappe correctement les caractères problématiques pour Turtle (quotes, backslashes, newlines).
- `only_markup_and_links(s)`: détecte si la valeur ne contient que du markup/liens sans texte résiduel.
- `sanitize_title_to_iri_local(title)`: convertit un titre wiki en CURIE local `kg-res:...` sûr pour Turtle.
- `wiki_value_to_rdf_normalized(value, pred, out)`: écrit des IRIs si uniquement des liens; sinon un littéral propre.
- `extract_infobox_block(wikitext)`: extrait le bloc {{Infobox ...}} en comptant les paires d’accolades.
- `parse_infobox(text)`: parse les arguments de l’infobox et retourne un dict clé → valeur.
- `sanitize_subject_iri(entity)`: construit l’IRI sujet `kg-res:...` à partir du nom d’entité.

Entrées/Sorties
- Entrée: fichiers `infobox_*.txt` dans `infoboxes/`; mapping via `property_map`.
- Sortie: `rdf/all_infoboxes.ttl` avec les préfixes `schema`, `dbp`, `kg-ont`, `kg-res`, `ex`, etc.

Prérequis
- Python 3.8+ et `wikitextparser`.
- Installation: `pip install -r requirements.txt` (ou `pip install wikitextparser`).

Utilisation
- Exécuter: `python testApiRequest/rdf_maker.py`
- Adapter `property_map` si nécessaire (ajouter/renommer des prédicats en fonction des champs d’infobox).
- Les valeurs faites uniquement de liens `[[...]]` deviennent des IRIs; sinon des littéraux nettoyés.

Notes
- Le sujet est typé `schema:Person` par défaut.
- Fallback: si aucune écriture n’a eu lieu pour une valeur, un littéral échappé via `ttl_escape` est produit.
- Les IRIs locaux pour valeurs utilisent `kg-res:`.
"""

def clean_value(v):
    v = re.sub(r'<br\s*/?>', ' ', v)
    v = re.sub(r'</?small[^>]*>', '', v)
    v = re.sub(r'</?(span|sup|sub|i|b)[^>]*>', '', v)
    v = re.sub(r'<ref[^>]*>.*?</ref>', '', v, flags=re.DOTALL)
    v = re.sub(r'<ref[^/>]*/>', '', v)

    v = v.replace('&nbsp;', ' ').replace('&amp;', '&')

    v = re.sub(r'\{\{SR\|(\d+)\}\}', r'SR \1', v)
    v = re.sub(r'\{\{TA\|(\d+)(\|[^\}]+)?\}\}', r'TA \1', v)
    v = re.sub(r'\{\{FA\|(\d+)(\|[^\}]+)?\}\}', r'FA \1', v)
    v = re.sub(r'\{\{SA\|(\d+)(\|[^\}]+)?\}\}', r'SA \1', v)
    v = re.sub(r'\{\{YT\|(\d+)(\|[^\}]+)?\}\}', r'YT \1', v)
    v = re.sub(r'\{\{FoA\|(\d+)(\|[^\}]+)?\}\}', r'FoA \1', v)

    v = re.sub(r'\{\{(IPA|fact|citation needed|cn)[^}]*\}\}', '', v, flags=re.IGNORECASE)

    return v.strip()

def ttl_escape(s: str) -> str:
    s = s.replace('"', "'")
    s = s.replace('\\', '\\\\').replace('\n', '\\n')
    return s.strip()

LINK_RE = re.compile(r'\[\[(.+?)(\|(.+?))?\]\]')

def only_markup_and_links(s: str) -> bool:
    tmp = re.sub(r'\[\[.+?\]\]', '', s)
    tmp = re.sub(r'\{\{.+?\}\}', '', tmp)
    tmp = re.sub(r'[\s,;:&/()\'"–-]+', '', tmp)
    return tmp == ''

def sanitize_title_to_iri_local(title: str) -> str:
    """Vers un CURIE local 'kg-res:Title_With_Underscores' sûr pour Turtle."""
    t = title.strip()
    t = t.replace(' ', '_')
    t = ''.join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in t)
    t = re.sub(r'_{2,}', '_', t)
    t = t.strip('_')
    if not t:
        t = 'unknown'
    return f"kg-res:{t}"

def wiki_value_to_rdf_normalized(value: str, pred: str, out) -> bool:
    """
    - Si valeur ne contient que liens wiki (aucun texte résiduel) → produire IRIs multiples.
    - Sinon → produire un seul littéral propre avec liens remplacés par leur libellé.
    Retourne True si quelque chose a été écrit.
    """
    original = value
    value = clean_value(value)

    links = list(LINK_RE.finditer(value))
    has_links = bool(links)

    if has_links and only_markup_and_links(value):
        for m in links:
            target = m.group(1).strip()
            iri = sanitize_title_to_iri_local(target)
            out.write(f"  ;\n  {pred} {iri}")
        return True
    else:
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', value)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = re.sub(r'\{\{.+?\}\}', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = ttl_escape(text)
        if text:
            out.write(f'  ;\n  {pred} "{text}"')
            return True
        return False
    
    
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
    parsed = wtp.parse(text)
    data = {}
    for t in parsed.templates:
        name = t.name.strip().lower()
        if name.startswith("infobox"):
            for arg in t.arguments:
                key = arg.name.strip()
                value = clean_value(arg.value.strip())
                data[key] = value
            break
    return data

property_map = {
    'name': 'schema:name',
    'birth': 'dbp:birthDate',
    'birthlocation': 'schema:birthPlace',
    'birthLocation': 'schema:birthPlace',
    'deathlocation': 'schema:deathPlace',
    'deathLocation': 'schema:deathPlace',
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
    'notableFor': 'schema:description',
    'race': 'kg-ont:race',
    'death': 'schema:deathDate',
}

def parse_embedded_infoboxes(data):
    """Récupère tous les contentN et labelN, retourne une liste de (label, infobox_dict)"""
    embedded = []
    for k, v in data.items():
        if k.startswith("content") and v.startswith("{{"):
            idx = k[len("content"):]
            label = data.get(f"label{idx}", "")
            parsed = wtp.parse(v)
            for t in parsed.templates:
                if t.name.strip().lower().startswith("song") or t.name.strip().lower().startswith("infobox"):
                    subdata = {}
                    for arg in t.arguments:
                        subdata[arg.name.strip()] = clean_value(arg.value.strip())
                    embedded.append((label, t.name.strip().lower(), subdata))
    return embedded

def get_type_from_template(template_name):
    if "song" in template_name:
        return "schema:MusicRecording"
    if "album" in template_name:
        return "schema:MusicAlbum"
    if "movie" in template_name:
        return "schema:Movie"
    if "game" in template_name:
        return "schema:VideoGame"
    if "book" in template_name:
        return "schema:Book"
    if "character" in template_name or "person" in template_name:
        return "kg-ont:Character"
    return "schema:CreativeWork"

def sanitize_subject_iri(entity: str) -> str:
    t = entity.strip()
    t = t.replace(' ', '_')
    t = ''.join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in t)
    t = re.sub(r'_{2,}', '_', t)
    t = t.strip('_')
    if not t:
        t = 'unknown'
    return f"kg-res:{t}"

output_file = os.path.join(output_dir, "all_infoboxes.ttl")
with open(output_file, "w", encoding="utf-8") as out:
    out.write("""@prefix kg-ont: <http://tolkien-kg.org/ontology/> .
@prefix kg-res: <http://tolkien-kg.org/resource/> .
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
            subj = sanitize_subject_iri(entity)

            embedded = parse_embedded_infoboxes(data)
            sub_iris = []

            for k in list(data.keys()):
                if k.startswith("content") or k.startswith("label"):
                    del data[k]

            out.write(f"{subj} a schema:CreativeWork")
            if "name" in data and data["name"]:
                out.write(f' ;\n  schema:name "{ttl_escape(data["name"])}"')
            else:
                out.write(f' ;\n  schema:name "{ttl_escape(entity)}"')
            for idx, (label, template, subdata) in enumerate(embedded):
                sub_iri = f"{subj}_{label.replace(' ', '_') or 'part'}"
                sub_iris.append(sub_iri)
                out.write(f" ;\n  schema:hasPart {sub_iri}")
            out.write(" .\n\n")

            for idx, (label, template, subdata) in enumerate(embedded):
                sub_iri = f"{subj}_{label.replace(' ', '_') or 'part'}"
                sub_type = get_type_from_template(template)
                out.write(f"{sub_iri} a {sub_type}")
                if "title" in subdata and subdata["title"]:
                    out.write(f' ;\n  schema:name "{ttl_escape(subdata["title"])}"')
                for k, v in subdata.items():
                    if not v or k == "title":
                        continue
                    pred = property_map.get(k, property_map.get(k.lower(), f"kg-ont:{k.replace(' ', '_')}"))
                    if not wiki_value_to_rdf_normalized(v, pred, out):
                        out.write(f'  ;\n  {pred} "{ttl_escape(v)}"')
                out.write(" .\n\n")

            if not embedded:
                main_type = get_type_from_template("infobox character" if "character" in data else "infobox")
                out.write(f"{subj} a {main_type}")
                for k, v in data.items():
                    if not v:
                        continue
                    pred = property_map.get(k, property_map.get(k.lower(), f"kg-ont:{k.replace(' ', '_')}"))
                    if not wiki_value_to_rdf_normalized(v, pred, out):
                        out.write(f'  ;\n  {pred} "{ttl_escape(v)}"')
                out.write(" .\n\n")

    print(f"All infoboxes written to {output_file}")
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
    """Vers un CURIE local 'kg-res:Title_With_Underscores' sûr pour Turtle, sans ponctuation ni accents."""
    import unicodedata
    t = title.strip()
    t = t.replace(' ', '_')
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = ''.join(c if c.isalnum() or c in ('_', '.') else '_' for c in t)
    t = re.sub(r'_{2,}', '_', t)
    t = t.strip('_')
    if not t:
        t = 'unknown'
    return f"kg-res:{t}"

def wiki_value_to_rdf_normalized(value: str, pred: str, out, force_literal: bool = False) -> bool:
    """
    - Si `force_literal` est vrai → toujours écrire un littéral nettoyé.
    - Sinon, si valeur ne contient que des liens wiki → produire IRIs multiples.
    - Sinon → produire un seul littéral propre avec liens remplacés par leur libellé.
    Retourne True si quelque chose a été écrit.
    """
    original = value
    value = clean_value(value)

    links = list(LINK_RE.finditer(value))
    has_links = bool(links)

    if not force_literal and has_links and only_markup_and_links(value):
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

LITERAL_ONLY_PROPS = {
    'kg-ont:weapons', 'kg-ont:steed', 'kg-ont:birthDate', 'kg-ont:deathDate',
    'kg-ont:height'
}
LOCATION_PROPS = {
    'kg-ont:birthLocation', 'kg-ont:deathLocation',
    'schema:birthPlace', 'schema:deathPlace', 'schema:location'
}
RELATION_PROPS = {'kg-ont:parentage', 'kg-ont:children', 'kg-ont:spouse'}
ALLOWED_GENDERS = {
    'male': 'Male',
    'female': 'Female',
    'stallion': 'Stallion',
    'male (presumably)': 'Male (presumably)'
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


def family_values_to_entries(value: str):
    """Extrait une liste (iri, label) pour les familles, qu'il y ait des liens ou du texte simple."""
    val = clean_value(value)
    links = list(LINK_RE.finditer(val))
    entries = []
    if links:
        for m in links:
            target = m.group(1).strip()
            label = (m.group(3) or target).strip()
            if not label:
                continue
            iri = sanitize_title_to_iri_local(target)
            entries.append((iri, label))
    else:
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', val)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        text = re.sub(r'\{\{.+?\}\}', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
        if text:
            parts = [p.strip() for p in re.split(r'[;,/]| and ', text) if p.strip()]
            for part in parts:
                iri = sanitize_title_to_iri_local(part)
                entries.append((iri, part))
    return entries


def process_family(value: str, out, houses_dict) -> bool:
    """Écrit kg-ont:family vers des IRIs de maisons et enregistre les labels à matérialiser plus bas."""
    entries = family_values_to_entries(value)
    wrote = False
    for iri, label in entries:
        houses_dict.setdefault(iri, label)
        out.write(f"  ;\n  kg-ont:family {iri}")
        wrote = True
    return wrote


def should_skip_location(value: str) -> bool:
    """Ignore les lieux textuels non reliables (unknown/unknown place/never)."""
    v = value.strip().lower()
    return v in {"", "unknown", "n/a", "none", "never", "nowhere"}


def should_skip_relation(value: str) -> bool:
    """Ignore les relations non renseignées ou textuelles (unknown/never married/none)."""
    v = value.strip().lower()
    if v in {"", "unknown", "n/a", "none"}:
        return True
    if "never married" in v:
        return True
    if "unknown" in v and "parent" in v:
        return True
    if "other foul creatures" in v:
        return True
    if "[[" not in value:
        return True
    return False

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
    if "character" in template_name or "characters" in template_name or "person" in template_name:
        return "kg-ont:Character"
    return "schema:CreativeWork"

def sanitize_subject_iri(entity: str) -> str:
    import unicodedata
    t = entity.strip()
    t = t.replace(' ', '_')
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = ''.join(c if c.isalnum() or c in ('_', '.') else '_' for c in t)
    t = re.sub(r'_{2,}', '_', t)
    t = t.strip('_')
    if not t:
        t = 'unknown'
    return f"kg-res:{t}"

houses_to_emit = {}
locations_to_emit = {}
characters_to_emit = {}
subjects_emitted = set()

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
            subjects_emitted.add(subj)

            embedded = parse_embedded_infoboxes(data)
            sub_iris = []

            for k in list(data.keys()):
                if k.startswith("content") or k.startswith("label"):
                    del data[k]

            if embedded:
                main_type = "schema:CreativeWork"
            else:
                main_type = get_type_from_template("infobox character" if any(k in data for k in ['gender', 'birth', 'death', 'race', 'parentage']) else "infobox")
            
            out.write(f"{subj} a {main_type}")
            if "name" in data and data["name"]:
                out.write(f' ;\n  schema:name "{ttl_escape(data["name"])}"')
            else:
                out.write(f' ;\n  schema:name "{ttl_escape(entity)}"')
            
            if embedded:
                for idx, (label, template, subdata) in enumerate(embedded):
                    sub_iri = f"{subj}_{label.replace(' ', '_') or 'part'}"
                    sub_iris.append(sub_iri)
                    out.write(f" ;\n  schema:hasPart {sub_iri}")
                out.write(" .\n\n")
            else:
                for k, v in data.items():
                    if not v or k == "name": 
                        continue
                    pred = property_map.get(k, property_map.get(k.lower(), f"kg-ont:{k.replace(' ', '_')}"))

                    if pred == "schema:gender":
                        gender_key = clean_value(v).strip().lower()
                        if gender_key not in ALLOWED_GENDERS:
                            continue
                        out.write(f'  ;\n  {pred} "{ttl_escape(ALLOWED_GENDERS[gender_key])}"')
                        continue

                    if pred == "kg-ont:family":
                        if process_family(v, out, houses_to_emit):
                            continue

                    if pred in LOCATION_PROPS:
                        if should_skip_location(v):
                            continue
                        val = clean_value(v)
                        links = list(LINK_RE.finditer(val))
                        if not links:
                            continue
                        wrote_loc = False
                        for m in links:
                            target = m.group(1).strip()
                            label = (m.group(3) or target).strip()
                            if not label:
                                continue
                            iri = sanitize_title_to_iri_local(target)
                            locations_to_emit.setdefault(iri, label)
                            out.write(f"  ;\n  {pred} {iri}")
                            wrote_loc = True
                        if wrote_loc:
                            continue
                        else:
                            continue

                    if pred in RELATION_PROPS:
                        if should_skip_relation(v):
                            continue
                        val = clean_value(v)
                        links = list(LINK_RE.finditer(val))
                        if not links:
                            continue
                        for idx_link, m in enumerate(links):
                            if pred == "kg-ont:spouse" and idx_link > 0:
                                break
                            target = m.group(1).strip()
                            label_rel = (m.group(3) or target).strip()
                            iri = sanitize_title_to_iri_local(target)
                            if label_rel:
                                characters_to_emit.setdefault(iri, label_rel)
                            out.write(f"  ;\n  {pred} {iri}")
                        continue

                    force_literal = pred in LITERAL_ONLY_PROPS
                    if not wiki_value_to_rdf_normalized(v, pred, out, force_literal=force_literal):
                        out.write(f'  ;\n  {pred} "{ttl_escape(v)}"')
                out.write(" .\n\n")

            for idx, (label, template, subdata) in enumerate(embedded):
                sub_iri = f"{subj}_{label.replace(' ', '_') or 'part'}"
                sub_type = get_type_from_template(template)
                out.write(f"{sub_iri} a {sub_type}")
                subjects_emitted.add(sub_iri)
                if "title" in subdata and subdata["title"]:
                    out.write(f' ;\n  schema:name "{ttl_escape(subdata["title"])}"')
                for k, v in subdata.items():
                    if not v or k == "title":
                        continue
                    pred = property_map.get(k, property_map.get(k.lower(), f"kg-ont:{k.replace(' ', '_')}"))
                    if pred == "schema:gender":
                        gender_key = clean_value(v).strip().lower()
                        if gender_key not in ALLOWED_GENDERS:
                            continue
                        out.write(f'  ;\n  {pred} "{ttl_escape(ALLOWED_GENDERS[gender_key])}"')
                        continue
                    if pred == "kg-ont:family":
                        if process_family(v, out, houses_to_emit):
                            continue
                    if pred in LOCATION_PROPS:
                        if should_skip_location(v):
                            continue
                        val = clean_value(v)
                        links = list(LINK_RE.finditer(val))
                        if not links:
                            continue
                        wrote_loc = False
                        for m in links:
                            target = m.group(1).strip()
                            label_loc = (m.group(3) or target).strip()
                            if not label_loc:
                                continue
                            iri = sanitize_title_to_iri_local(target)
                            locations_to_emit.setdefault(iri, label_loc)
                            out.write(f"  ;\n  {pred} {iri}")
                            wrote_loc = True
                        if wrote_loc:
                            continue
                        else:
                            continue
                    if pred in RELATION_PROPS:
                        if should_skip_relation(v):
                            continue
                        val = clean_value(v)
                        links = list(LINK_RE.finditer(val))
                        if not links:
                            continue
                        for idx_link, m in enumerate(links):
                            if pred == "kg-ont:spouse" and idx_link > 0:
                                break
                            target = m.group(1).strip()
                            label_rel = (m.group(3) or target).strip()
                            iri = sanitize_title_to_iri_local(target)
                            if label_rel:
                                characters_to_emit.setdefault(iri, label_rel)
                            out.write(f"  ;\n  {pred} {iri}")
                        continue
                    force_literal = pred in LITERAL_ONLY_PROPS
                    if not wiki_value_to_rdf_normalized(v, pred, out, force_literal=force_literal):
                        out.write(f'  ;\n  {pred} "{ttl_escape(v)}"')
                out.write(" .\n\n")

    for iri, label in locations_to_emit.items():
        out.write(f"{iri} a kg-ont:Location ;\n  rdfs:label \"{ttl_escape(label)}\" .\n\n")

    for iri, label in characters_to_emit.items():
        if iri in subjects_emitted:
            continue
        out.write(f"{iri} a kg-ont:Character ;\n  schema:name \"{ttl_escape(label)}\" .\n\n")

    for iri, label in houses_to_emit.items():
        out.write(f"{iri} a kg-ont:House ;\n  rdfs:label \"{ttl_escape(label)}\" .\n\n")

    print(f"All infoboxes written to {output_file}")
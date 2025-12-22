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
- `sanitize_title_to_iri_local(title)`: convertit un titre wiki en CURIE local `ex:...` sûr pour Turtle.
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
- Les IRIs locaux pour valeurs utilisent `ex:`; les sujets utilisent `kg-res:`.
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
    """Vers un CURIE local 'ex:Title_With_Underscores' sûr pour Turtle."""
    t = title.strip()
    t = t.replace(' ', '_')
    t = ''.join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in t)
    t = re.sub(r'_{2,}', '_', t)
    t = t.strip('_')
    if not t:
        t = 'unknown'
    return f"ex:{t}"

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

def sanitize_subject_iri(entity: str) -> str:
    """Nettoie le nom d'entité pour en faire un IRI valide."""
    t = entity.strip()
    t = t.replace(' ', '_')
    t = ''.join(c if c.isalnum() or c in ('_', '-', '.') else f'%{ord(c):02X}' for c in t)
    return f"kg-res:{t}"

output_file = os.path.join(output_dir, "all_infoboxes.ttl")
with open(output_file, "w", encoding="utf-8") as out:
    out.write("""@prefix kg-ont: <http://tolkien-kg.org/ontology/> .
@prefix kg-res: <http://tolkien-kg.org/resource/> .
@prefix ex: <http://example.org/> .
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
            out.write(f"{subj} a schema:Person")
            wrote_any = False
            for k, v in data.items():
                if not v:
                    continue
                pred = property_map.get(k.lower(), f"kg-ont:{k.replace(' ', '_')}")
                if not wiki_value_to_rdf_normalized(v, pred, out):
                    out.write(f'  ;\n  {pred} "{ttl_escape(v)}"')
                wrote_any = True
            out.write(" .\n\n")
            print(f"RDF triples added for {entity}")
    print(f"All infoboxes written to {output_file}")

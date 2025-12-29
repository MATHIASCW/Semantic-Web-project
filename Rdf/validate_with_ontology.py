from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL

"""
Module de validation des propriétés RDF contre une ontologie.
Ce module valide que toutes les propriétés utilisées dans un dataset RDF
sont correctement définies dans l'ontologie correspondante.
Fonctionnalité principale:
- Charge une ontologie Tolkien depuis un fichier TTL
- Charge un dataset RDF contenant des infoboxes depuis un fichier TTL
- Extrait toutes les propriétés utilisées du namespace "http://tolkien-kg.org/ontology/"
- Récupère toutes les propriétés définies dans l'ontologie (ObjectProperty et DatatypeProperty)
- Compare les deux ensembles pour identifier les propriétés utilisées mais non définies
- Affiche un rapport détaillé des propriétés manquantes ou une confirmation si tout est valide
Le script aide à maintenir la cohérence et la validité du graphe de connaissances
en détectant les incohérences entre l'ontologie et les données réelles.
"""

ontology = Graph()
ontology.parse("RdfData/tolkien-kg-ontology.ttl", format="turtle")

data = Graph()
data.parse("RdfData/all_infoboxes.ttl", format="turtle")

print(f"✅ Ontologie: {len(ontology)} triplets")
print(f"✅ Données: {len(data)} triplets")

KG_ONT = "http://tolkien-kg.org/ontology/"
used_props = set()
defined_props = set()

for s, p, o in data.triples((None, None, None)):
    if str(p).startswith(KG_ONT):
        used_props.add(str(p))

for s in ontology.subjects(RDF.type, OWL.ObjectProperty):
    defined_props.add(str(s))
for s in ontology.subjects(RDF.type, OWL.DatatypeProperty):
    defined_props.add(str(s))

undefined = used_props - defined_props
if undefined:
    print(f"\n⚠️  Propriétés utilisées mais NON définies dans l'ontologie:")
    for prop in sorted(undefined):
        print(f"  - {prop}")
else:
    print("\n✅ Toutes les propriétés kg-ont:* sont définies!")
"""
Extension automatique de l'ontologie Tolkien
Ajoute toutes les propriétés manquantes détectées dans le RDF
"""

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD

ontology = Graph()
ontology.parse("RdfData/tolkien-kg-ontology.ttl", format="turtle")

data = Graph()
data.parse("RdfData/all_infoboxes.ttl", format="turtle")

KG_ONT = Namespace("http://tolkien-kg.org/ontology/")
ontology.bind("kg-ont", KG_ONT)
ontology.bind("owl", OWL)
ontology.bind("rdfs", RDFS)
ontology.bind("xsd", XSD)

used_props = set()
defined_props = set()

for s, p, o in data.triples((None, None, None)):
    if str(p).startswith("http://tolkien-kg.org/ontology/"):
        used_props.add(str(p))

for s in ontology.subjects(RDF.type, OWL.ObjectProperty):
    defined_props.add(str(s))
for s in ontology.subjects(RDF.type, OWL.DatatypeProperty):
    defined_props.add(str(s))

undefined = sorted(used_props - defined_props)

print(f"🔍 Propriétés manquantes: {len(undefined)}\n")

for prop_uri in undefined:
    prop = URIRef(prop_uri)
    local_name = prop_uri.split("/")[-1]
    
    ontology.add((prop, RDF.type, OWL.DatatypeProperty))
    ontology.add((prop, RDFS.label, Literal(local_name.replace("_", " ").title())))
    ontology.add((prop, RDFS.comment, Literal(f"Propriété extraite automatiquement des infoboxes.")))
    ontology.add((prop, RDFS.range, XSD.string))
    
    print(f"  ✅ Ajouté: {local_name}")

output_file = "RdfData/tolkien-kg-ontology.ttl"
ontology.serialize(destination=output_file, format="turtle")

print(f"\n📄 Ontologie mise à jour: {output_file}")
print(f"📊 Total triplets: {len(ontology)}\n")

print("🔍 Revalidation...")
ontology2 = Graph()
ontology2.parse(output_file, format="turtle")

data2 = Graph()
data2.parse("RdfData/all_infoboxes.ttl", format="turtle")

used2 = set()
defined2 = set()

for s, p, o in data2.triples((None, None, None)):
    if str(p).startswith("http://tolkien-kg.org/ontology/"):
        used2.add(str(p))

for s in ontology2.subjects(RDF.type, OWL.ObjectProperty):
    defined2.add(str(s))
for s in ontology2.subjects(RDF.type, OWL.DatatypeProperty):
    defined2.add(str(s))

still_undefined = used2 - defined2

if still_undefined:
    print(f"❌ Encore {len(still_undefined)} propriétés non définies!")
else:
    print("✅✅✅ TOUTES les propriétés sont maintenant définies!\n")

from rdflib import Graph
from rdflib.namespace import RDF, OWL

"""
Module for validating RDF properties against an ontology.
This module validates that all properties used in an RDF dataset
are correctly defined in the corresponding ontology.
"""

ontology = Graph()
ontology.parse("RdfData/tolkien-kg-ontology.ttl", format="turtle")

data = Graph()
data.parse("RdfData/kg_full.ttl", format="turtle")

print(f"OK. Ontology: {len(ontology)} triples")
print(f"OK. Data: {len(data)} triples")

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
    print("\nProperties used but NOT defined in the ontology:")
    for prop in sorted(undefined):
        print(f"  - {prop}")
else:
    print("\nOK. All kg-ont:* properties are defined.")

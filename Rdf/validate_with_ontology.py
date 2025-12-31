from rdflib import Graph
from rdflib.namespace import RDF, RDFS, OWL

"""
Module for validating RDF properties against an ontology.
This module validates that all properties used in an RDF dataset
are correctly defined in the corresponding ontology.
Main functionality:
- Load a Tolkien ontology from a TTL file
- Load an RDF dataset containing infoboxes from a TTL file
- Extract all properties used from the "http://tolkien-kg.org/ontology/" namespace
- Retrieve all properties defined in the ontology (ObjectProperty and DatatypeProperty)
- Compare the two sets to identify properties used but not defined
- Display a detailed report of missing properties or confirmation if all is valid
The script helps maintain the consistency and validity of the knowledge graph
by detecting inconsistencies between the ontology and actual data.
"""

ontology = Graph()
ontology.parse("RdfData/tolkien-kg-ontology.ttl", format="turtle")

data = Graph()
data.parse("RdfData/all_infoboxes.ttl", format="turtle")

print(f"✅ Ontology: {len(ontology)} triples")
print(f"✅ Data: {len(data)} triples")

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
    print(f"\n⚠️  Properties used but NOT defined in the ontology:")
    for prop in sorted(undefined):
        print(f"  - {prop}")
else:
    print("\n✅ All kg-ont:* properties are defined!")
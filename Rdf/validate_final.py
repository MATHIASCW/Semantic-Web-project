"""Final SHACL validation with relaxed constraints."""

from pyshacl import validate
from rdflib import Graph

print("Loading RDF data...")
data = Graph()
data.parse("RdfData/kg_full.ttl", format="turtle")
print(f"OK. {len(data)} triples loaded")

print("\nLoading SHACL shapes...")
shapes = Graph()
shapes.parse("RdfData/tolkien-shapes.ttl", format="turtle")
print(f"OK. {len(shapes)} shapes loaded")

print("\nRunning SHACL validation...")
conforms, results, text = validate(
    data,
    shacl_graph=shapes,
    inference="rdfs",
    abort_on_first=False,
)

print(f"\n{'=' * 60}")
print("VALIDATION RESULT")
print(f"{'=' * 60}")
print(f"\nOK. Conforms: {conforms}")

if not conforms:
    violations = text.count("Constraint Violation")
    print(f"Number of violations: {violations}")
    print(f"\n{'=' * 60}")
    print("FIRST VIOLATIONS:")
    print(f"{'=' * 60}\n")
    print(text[:2000])
else:
    print("\nNO SHACL VIOLATIONS!")
    print("OK. The RDF conforms to the shapes.")
    print("\nFinal statistics:")
    print(f"  - RDF triples: {len(data)}")
    print(f"  - SHACL triples: {len(shapes)}")
    print("  - Conformity: 100%")

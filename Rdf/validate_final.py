"""Final SHACL validation with relaxed constraints"""

from pyshacl import validate
from rdflib import Graph

print("📂 Loading RDF data...")
data = Graph()
data.parse('RdfData/all_infoboxes.ttl', format='turtle')
print(f"✅ {len(data)} triples loaded")

print("\n📋 Loading SHACL shapes...")
shapes = Graph()
shapes.parse('RdfData/tolkien-shapes.ttl', format='turtle')
print(f"✅ {len(shapes)} shapes loaded")

print("\n🔍 Running SHACL validation...")
conforms, results, text = validate(
    data, 
    shacl_graph=shapes, 
    inference='rdfs',
    abort_on_first=False
)

print(f"\n{'='*60}")
print(f"VALIDATION RESULT")
print(f"{'='*60}")
print(f"\n✅ Conforms: {conforms}")

if not conforms:
    violations = text.count("Constraint Violation")
    print(f"📊 Number of violations: {violations}")
    print(f"\n{'='*60}")
    print("FIRST VIOLATIONS:")
    print(f"{'='*60}\n")
    print(text[:2000])
else:
    print("\n🎉🎉🎉 NO SHACL VIOLATIONS!")
    print("✅ The RDF is perfectly conforms to the shapes!")
    print("\n📊 Final statistics:")
    print(f"   - RDF triples: {len(data)}")
    print(f"   - SHACL triples: {len(shapes)}")
    print(f"   - Conformity: 100%")

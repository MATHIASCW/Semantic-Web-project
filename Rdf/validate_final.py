"""Validation SHACL finale avec contraintes assouplies"""

from pyshacl import validate
from rdflib import Graph

print("📂 Chargement des données RDF...")
data = Graph()
data.parse('RdfData/all_infoboxes.ttl', format='turtle')
print(f"✅ {len(data)} triplets chargés")

print("\n📋 Chargement des shapes SHACL...")
shapes = Graph()
shapes.parse('RdfData/tolkien-shapes.ttl', format='turtle')
print(f"✅ {len(shapes)} shapes chargés")

print("\n🔍 Validation SHACL en cours...")
conforms, results, text = validate(
    data, 
    shacl_graph=shapes, 
    inference='rdfs',
    abort_on_first=False
)

print(f"\n{'='*60}")
print(f"RÉSULTAT DE LA VALIDATION")
print(f"{'='*60}")
print(f"\n✅ Conforme: {conforms}")

if not conforms:
    violations = text.count("Constraint Violation")
    print(f"📊 Nombre de violations: {violations}")
    print(f"\n{'='*60}")
    print("PREMIÈRES VIOLATIONS:")
    print(f"{'='*60}\n")
    print(text[:2000])
else:
    print("\n🎉🎉🎉 AUCUNE VIOLATION SHACL!")
    print("✅ Le RDF est parfaitement conforme aux shapes!")
    print("\n📊 Statistiques finales:")
    print(f"   - Triplets RDF: {len(data)}")
    print(f"   - Triplets SHACL: {len(shapes)}")
    print(f"   - Conformité: 100%")

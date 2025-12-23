from pyshacl import validate
from rdflib import Graph
data = Graph().parse("rdf/all_infoboxes.ttl", format="turtle")
shapes = Graph().parse("rdf/tolkien-shapes.ttl", format="turtle")
r = validate(data_graph=data, shacl_graph=shapes, inference='rdfs', serialize_report_graph=True)
conforms, results_text, report_graph = r
print(results_text)
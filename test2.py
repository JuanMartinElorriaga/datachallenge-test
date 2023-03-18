from py2neo import Graph, Node, Relationship
import xml.etree.ElementTree as ET

# Connect to Neo4j graph database
graph = Graph(uri="bolt://localhost:7687", auth=("neo4j", "password"))

# Define XML namespaces
namespaces = {
    "uniprot": "http://uniprot.org/uniprot",
    "pdb": "http://uniprot.org/pdb",
    "xref": "http://uniprot.org/xref",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}

# Parse UniProt XML file
tree = ET.parse("uniprot.xml")
root = tree.getroot()

# Loop through all protein entries
for entry in root.findall("uniprot:entry", namespaces):
    # Extract protein information
    accession = entry.find("uniprot:accession", namespaces).text
    name = entry.find("uniprot:name", namespaces).text
    sequence = entry.find("uniprot:sequence", namespaces).text

    # Create protein node
    protein_node = Node("Protein", accession=accession, name=name, sequence=sequence)
    graph.create(protein_node)

    # Loop through all protein-protein interactions
    for interaction in entry.findall("uniprot:interactionList/uniprot:interaction", namespaces):
        # Extract interaction information
        partner_accession = interaction.find("uniprot:interactant/uniprot:iden", namespaces).text

        # Create partner protein node if it doesn't exist
        partner_node = graph.nodes.match("Protein", accession=partner_accession).first()
        if not partner_node:
            partner_entry = graph.run("MATCH (p:Protein) WHERE p.accession = $accession RETURN p", accession=partner_accession).data()
            if partner_entry:
                partner_node = partner_entry[0]["p"]
            else:
                partner_name = interaction.find("uniprot:interactant/uniprot:label", namespaces).text
                partner_node = Node("Protein", accession=partner_accession, name=partner_name)
                graph.create(partner_node)

        # Create protein-protein interaction relationship
        interaction_type = interaction.find("uniprot:interactionType", namespaces).text
        interaction_node = Relationship(protein_node, interaction_type, partner_node)
        graph.create(interaction_node)

# CONTINUATION
# Create indexes for faster querying
graph.run("CREATE INDEX ON :Protein(accession)")
graph.run("CREATE INDEX ON :Protein(name)")

# Query the database for proteins and their interactions
query = """
MATCH (p:Protein)-[r]->(p2:Protein)
WHERE p.accession = $accession
RETURN p, r, p2
"""
result = graph.run(query, accession="P12345").data()

# Print out the results
for record in result:
    print(record["p"]["name"], record["r"].type, record["p2"]["name"])
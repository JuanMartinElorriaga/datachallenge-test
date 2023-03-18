# Coding Challenge: Process follow through

## High level steps

- Parse the UniProt XML file to extract the relevant data.
- Transform the extracted data into a format that can be easily ingested into Neo4j, such as a set of CSV files.
- Use a Neo4j driver or client library (such as Py2neo for Python) to connect to the Neo4j database and create the necessary nodes and relationships based on the data.
- Optionally, add any necessary indexes or constraints to the Neo4j database to optimize queries.

This code connects to a Neo4j graph database, reads in a UniProt XML file, creates protein nodes for each entry, and creates protein-protein interaction relationships between proteins. The code checks if a partner protein node already exists in the database before creating a new one. It then creates a relationship between the two proteins with the type of interaction extracted from the XML file. The code uses Py2neo to interact with the Neo4j database, and the ElementTree module to parse the UniProt XML file.

This code creates two indexes on the accession and name properties of the Protein nodes for faster querying. It then performs a query to retrieve all proteins and their interactions for a specific protein (in this case, the protein with accession "P12345"). The results are printed out, showing the names of the proteins and the type of interaction between them.

## Docker 
### Neo4j
Code: 

```
docker run --publish=7474:7474 --publish=7687:7687 --env=NEO4J_AUTH=none --volume=$HOME/neo4j/data:/data neo4j
```
Volumes:
- /data
- /logs

Extra:
- The `--restart` always option sets the Neo4j container (and Neo4j) to restart automatically whenever the Docker daemon is restarted. To remove it: `docker update --restart=no <containerID>`


## Graph database
- Mindset de las query: comenzar con un nodo específico en mente. Luego, usar pattern matching para encontrar nodos relacionados con el nodo original. Finalmente, 


# References
- (Dockerhub Neo4j image)[https://hub.docker.com/_/neo4j/]

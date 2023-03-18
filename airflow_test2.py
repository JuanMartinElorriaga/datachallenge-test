from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.neo4j_operator import Neo4jOperator
from datetime import datetime, timedelta
from py2neo import Graph
from lxml import etree
import os

# Default arguments for the DAG
default_args = {
    'owner'           : 'airflow',
    'depends_on_past' : False,
    'start_date'      : datetime(2023, 3, 18),
    'email_on_failure': False,
    'email_on_retry'  : False,
    'retries'         : 1,
    'retry_delay'     : timedelta(minutes=5),
}

# Define the DAG object
dag = DAG(
    'uniprot_neo4j_pipeline',
    default_args      = default_args,
    schedule_interval = timedelta(days=1),
)

# Define the BashOperator to download the UniProt XML file
download_op = BashOperator(
    task_id      = 'download_uniprot_xml',
    bash_command = 'curl -o uniprot.xml https://www.uniprot.org/uniprot/?query=*&format=xml', #TODO change for url github
    dag          = dag,
)

# Define the PythonOperator to process the UniProt XML file and store the data in Neo4j
def process_uniprot_xml():
    # Connect to the Neo4j graph database
    neo4j_uri      = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user     = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
    graph          = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))

    # Parse the UniProt XML file
    xml_file = open('uniprot.xml', 'rb')
    tree     = etree.parse(xml_file)

    # Extract the relevant data from the XML file and store it in Neo4j
    for entry in tree.xpath('//entry'):
        accession   = entry.get('accession')
        name        = entry.find('name').text
        description = entry.find('protein/recommendedName/fullName').text
        gene        = entry.find('gene/name').text

        # Create a Cypher query to create a new node for the protein and its properties
        cypher_query = f"CREATE (p:Protein {{accession: '{accession}', name: '{name}', description: '{description}', gene: '{gene}'}})"

        # Execute the query using the Neo4j driver
        graph.run(cypher_query)

# Define the PythonOperator to process the UniProt XML file
process_op = PythonOperator(
    task_id         = 'process_uniprot_xml',
    python_callable = process_uniprot_xml,
    dag             = dag,
)

# Define the Neo4jOperator to create an index on the Protein nodes
create_index_op = Neo4jOperator(
    task_id = 'create_index',
    query   = 'CREATE INDEX ON :Protein(accession)',
    uri     = os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
    auth    = (os.environ.get('NEO4J_USER', 'neo4j'), os.environ.get('NEO4J_PASSWORD', 'password')),
    dag     = dag,
)

# Define the PythonOperator to query the Neo4j graph database
def query_neo4j():
    # Connect to the Neo4j graph database
    neo4j_uri      = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user     = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
    graph          = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))

    # Define a Cypher query to retrieve the number of Protein nodes in the graph
    cypher_query = 'MATCH (p:Protein) RETURN count(p)'

    # Execute the query using the Neo4j driver and print the result
    result = graph.run(cypher_query).evaluate()
    print(f'Number of Protein nodes: {result}')

# Define the PythonOperator to query the Neo4j graph database
query_op = PythonOperator(
    task_id         = 'query_neo4j',
    python_callable = query_neo4j,
    dag             = dag,
)

# Set the dependencies between the tasks
download_op >> process_op >> create_index_op >> query_op
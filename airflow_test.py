from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
import os

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 18),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG object
dag = DAG(
    'uniprot_neo4j_pipeline',
    default_args=default_args,
    schedule_interval=timedelta(days=1),
)

# Define the BashOperator to download the UniProt XML file
download_op = BashOperator(
    task_id='download_uniprot_xml',
    bash_command='curl -o uniprot.xml https://www.uniprot.org/uniprot/?query=*&format=xml',
    dag=dag,
)

# Define the PythonOperator to process the UniProt XML file and store the data in Neo4j
def process_uniprot_xml():
    # Import the required libraries
    from py2neo import Graph
    from lxml import etree

    # Connect to the Neo4j graph database
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
    graph = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))

    # Parse the UniProt XML file
    xml_file = open('uniprot.xml', 'rb')
    tree = etree.parse(xml_file)

    # Extract the relevant data from the XML file and store it in Neo4j
    for entry in tree.xpath('//entry'):
        accession = entry.get('accession')
        name = entry.find('name').text
        description = entry.find('protein/recommendedName/fullName').text
        gene = entry.find('gene/name').text

        # Create a Cypher query to create a new node for the protein and its properties
        cypher_query = f"CREATE (p:Protein {{accession: '{accession}', name: '{name}', description: '{description}', gene: '{gene}'}})"

        # Execute the query using the Neo4j driver
        graph.run(cypher_query)

# Define the PythonOperator to process the UniProt XML file
process_op = PythonOperator(
    task_id='process_uniprot_xml',
    python_callable=process_uniprot_xml,
    dag=dag,
)

# Set the dependencies between the tasks
download_op >> process_op

"""
This DAG downloads the UniProt XML file using a BashOperator, 
then processes the XML file using a PythonOperator that connects to 
a Neo4j graph database and extracts the relevant data from the XML file, 
and finally stores the data in Neo4j using Cypher queries. 
The DAG runs once a day by default, but this can be adjusted to 
meet the requirements of the pipeline.

"""
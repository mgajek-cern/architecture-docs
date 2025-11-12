#!/usr/bin/env python3
"""
Complete Rucio Development Environment Deployment Diagram
Based on the full Docker Compose setup including all optional services
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import PostgreSQL, MySQL
from diagrams.onprem.monitoring import Grafana
from diagrams.onprem.client import Users
from diagrams.onprem.queue import ActiveMQ
from diagrams.generic.storage import Storage
from diagrams.onprem.compute import Server

# Configure diagram attributes
graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "pad": "2.0",
    "splines": "ortho"
}

node_attr = {
    "fontsize": "11",
    "fontname": "Helvetica"
}

edge_attr = {
    "fontsize": "10"
}

with Diagram("Rucio Development Environment - Complete", 
             filename="./deployment",
             show=False,
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             direction="TB"):
    
    # Users
    users = Users("Developers")
    
    # Core Rucio System
    with Cluster("Core Rucio Services"):
        rucio_dev = Server("Rucio Server")
        rucio_client = Server("Rucio Client")
        
    # Database Options
    with Cluster("Database Options"):
        rucio_db = PostgreSQL("PostgreSQL")
        mysql8 = MySQL("MySQL 8")
        oracle_db = Server("Oracle XE")
        
    # Storage Services (RSEs)
    with Cluster("Storage Services (RSEs)"):
        xrd_cluster = Storage("XRootD Cluster")
        webdav = Server("WebDAV")
        ssh_server = Server("SSH Transfer")
        minio = Server("MinIO S3")
        
    # Transfer Management
    with Cluster("File Transfer Service"):
        fts = Server("FTS Server")
        fts_db = MySQL("FTS Database")
        
    # IAM & Authentication
    with Cluster("Identity & Access Management"):
        keycloak = Server("Keycloak")
        indigo_iam = Server("INDIGO IAM")
        iam_db = MySQL("IAM Database")
        
    # Messaging & Events
    with Cluster("Messaging"):
        activemq = ActiveMQ("ActiveMQ")
        
    # Monitoring Stack
    with Cluster("Monitoring"):
        grafana = Grafana("Grafana")
        influxdb = Server("InfluxDB")
        graphite = Server("Graphite")
        
    # Logging & Search
    with Cluster("Logging & Analytics"):
        kibana = Server("Kibana")
        logstash = Server("Logstash")
        elasticsearch = Server("Elasticsearch")
        
    # Metadata Services
    with Cluster("External Metadata"):
        mongo = Server("MongoDB")
        postgres_meta = PostgreSQL("PostgreSQL Meta")
        elasticsearch_meta = Server("Elasticsearch Meta")
    
    # Connections (no descriptions as requested)
    users >> rucio_dev
    
    # Core database connections
    rucio_dev >> rucio_db
    
    # Storage connections
    rucio_dev >> [xrd_cluster, webdav, ssh_server, minio]
    
    # Transfer service
    rucio_dev >> fts
    fts >> fts_db
    
    # IAM connections
    rucio_dev >> [keycloak, indigo_iam]
    keycloak >> iam_db
    indigo_iam >> iam_db
    
    # Messaging
    rucio_dev >> activemq
    
    # Monitoring
    rucio_dev >> [influxdb, graphite]
    
    # Logging
    rucio_dev >> logstash
    logstash >> elasticsearch
    elasticsearch >> kibana
    
    # External metadata
    rucio_dev >> [mongo, postgres_meta, elasticsearch_meta]

print("Complete Rucio development environment diagram generated!")
print("Includes all services from Docker Compose:")
print("- Core: Rucio server + client containers")
print("- Databases: PostgreSQL, MySQL, Oracle options")
print("- Storage: XRootD, WebDAV, SSH, MinIO S3")
print("- IAM: Keycloak + INDIGO IAM with shared database")
print("- Transfer: FTS3 with MySQL backend") 
print("- Messaging: ActiveMQ")
print("- Monitoring: Grafana + InfluxDB + Graphite")
print("- Logging: ELK stack")
print("- External metadata: MongoDB, PostgreSQL, Elasticsearch")
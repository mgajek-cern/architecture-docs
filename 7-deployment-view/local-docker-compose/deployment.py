#!/usr/bin/env python3
"""
Rucio Development Environment Deployment Diagram
Creates a visual representation of the Rucio dev setup with all service components
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import PostgreSQL, MySQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.onprem.network import Internet
from diagrams.onprem.client import Users
from diagrams.onprem.queue import ActiveMQ
from diagrams.generic.blank import Blank
from diagrams.generic.network import Router
from diagrams.generic.compute import Rack
from diagrams.generic.storage import Storage
from diagrams.programming.language import Python
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

with Diagram("Rucio Development Environment", 
             filename="./deployment",
             show=False,
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             direction="TB"):
    
    # Users
    users = Users("Developers &\nTesting Users")
    
    # Core Rucio System
    with Cluster("Core Rucio Services"):
        rucio_dev = Server("Rucio Server\nrucio-dev\n8443→443")
        rucio_db = PostgreSQL("PostgreSQL\nRucio DB\n5432")
        daemons = Python("Rucio Daemons\nBackground Services")
        
    # Storage Services
    with Cluster("Storage Services (RSEs)"):
        xrootd1 = Storage("XRootD-1\ndev-xrd1\n1094")
        xrootd2 = Storage("XRootD-2\ndev-xrd2\n1095") 
        xrootd3 = Storage("XRootD-3\ndev-xrd3\n1096")
        xrootd4 = Storage("XRootD-4\ndev-xrd4\n1097")
        xrootd5 = Storage("XRootD-5\ndev-xrd5\n1098/8098")
        webdav = Server("WebDAV\ndev-web1\n8099")
        ssh_server = Server("SSH Transfer\ndev-ssh1\n2222→22")
        
    # Transfer Management
    with Cluster("File Transfer Service"):
        fts = Server("FTS Server\ndev-fts\n8446/8449")
        fts_db = MySQL("FTS MySQL\nDB\n3306")
        
    # Messaging (for specific daemon operations)
    with Cluster("Messaging & Events"):
        activemq = ActiveMQ("ActiveMQ\nMessage Broker\n61613")
        
    # Monitoring Stack
    with Cluster("Monitoring & Metrics"):
        influxdb = Server("InfluxDB\nTime Series DB\n8086")
        graphite = Server("Graphite\nMetrics DB\n8080")
        grafana = Grafana("Grafana\nDashboards\n3000")
        
    # Logging Stack  
    with Cluster("Logging & Analytics"):
        logstash = Server("Logstash\nLog Processor\n5044")
        elasticsearch = Server("Elasticsearch\nSearch Engine\n9200/9300")
        kibana = Server("Kibana\nLog Analytics\n5601")
    
    # User interactions
    users >> Edge(label="HTTPS:8443", color="blue") >> rucio_dev
    
    # Core Rucio connections (primary communication via database)
    rucio_dev >> Edge(label="SQL", color="red") >> rucio_db
    daemons >> Edge(label="database ops\n(primary)", color="red") >> rucio_db
    
    # Storage connections
    rucio_dev >> Edge(label="XRootD", color="green") >> [xrootd1, xrootd2, xrootd3, xrootd4, xrootd5]
    rucio_dev >> Edge(label="WebDAV", color="green") >> webdav
    rucio_dev >> Edge(label="SSH", color="green") >> ssh_server
    
    # Transfer service
    rucio_dev >> Edge(label="FTS control", color="orange") >> fts
    fts >> Edge(label="SQL", color="red") >> fts_db
    
    # Messaging (secondary, specific operations)
    rucio_dev >> Edge(label="events", color="purple", style="dashed") >> activemq
    daemons >> Edge(label="consume events\n(secondary)", color="purple", style="dashed") >> activemq
    
    # Monitoring
    rucio_dev >> Edge(label="metrics", color="gray") >> influxdb
    rucio_dev >> Edge(label="metrics", color="gray") >> graphite
    influxdb >> Edge(color="gray") >> grafana
    graphite >> Edge(color="gray") >> grafana
    
    # Logging
    rucio_dev >> Edge(label="logs", color="brown") >> logstash
    logstash >> Edge(color="brown") >> elasticsearch
    elasticsearch >> Edge(color="brown") >> kibana

print("Rucio development environment diagram generated!")
print("Components:")
print("- Core: Rucio server + PostgreSQL database")
print("- Storage: 5x XRootD + WebDAV + SSH transfer endpoints") 
print("- Transfer: FTS3 with MySQL backend")
print("- Messaging: ActiveMQ for daemon communication")
print("- Monitoring: InfluxDB + Graphite + Grafana")
print("- Logging: ELK stack (Elasticsearch + Logstash + Kibana)")
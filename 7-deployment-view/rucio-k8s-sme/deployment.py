#!/usr/bin/env python3
"""
Rucio IT Infrastructure Deployment Diagram
Creates a visual representation of the Rucio IT architecture using the diagrams library
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.k8s.compute import Deployment, Pod, Job, ReplicaSet
from diagrams.k8s.network import Service, Ingress
from diagrams.k8s.storage import PersistentVolume, StorageClass
from diagrams.k8s.rbac import ServiceAccount
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Prometheus
from diagrams.onprem.vcs import Git
from diagrams.onprem.security import Vault
from diagrams.onprem.network import Internet
from diagrams.onprem.client import Users
from diagrams.aws.network import CloudFront
from diagrams.generic.blank import Blank
from diagrams.generic.os import Ubuntu
from diagrams.generic.storage import Storage
from diagrams.programming.language import Python

# Configure diagram attributes
graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "pad": "2.0",
    "splines": "ortho"
}

node_attr = {
    "fontsize": "12",
    "fontname": "Helvetica"
}

edge_attr = {
    "fontsize": "10"
}

with Diagram("Rucio IT Deployment Architecture", 
             filename="./rucio-k8s-sme-deployment", 
             show=False,
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             direction="TB"):
    
    # External users and services
    users = Users("Experiment Users")
    internet = Internet("Internet")
    
    # External services cluster
    with Cluster("External Services"):
        cern_sso = ServiceAccount("CERN SSO\nauth.cern.ch")
        fts_service = Service("FTS3 Transfer\nfts3-pilot.cern.ch")
        dns_service = Service("External DNS\nip-dns-0.cern.ch")
        
    # Control plane cluster
    with Cluster("ArgoCD Control Plane"):
        argo_server = Deployment("ArgoCD Server\nargo.rucioit.cern.ch")
        argo_repo = Pod("ArgoCD Repo Server")
        vault_plugin = Pod("Vault Plugin")
        
        vault = Vault("HashiCorp Vault\nwoger-vault.cern.ch")
        
        argo_server >> argo_repo >> vault_plugin
        vault_plugin >> Edge(style="dashed", label="secrets") >> vault
    
    # Database services
    with Cluster("Database Layer"):
        dbod = PostgreSQL("DBOD PostgreSQL\nper experiment")
        
    # Per-experiment deployment
    with Cluster("Experiment Cluster (ship, ams02, na62, etc.)"):
        
        # Rucio core services
        with Cluster("Rucio Core Services"):
            rucio_server = Deployment("Rucio Server\n{exp}-server.rucioit.cern.ch")
            rucio_auth = Deployment("Rucio Auth\n{exp}-auth.rucioit.cern.ch")
            rucio_webui = Deployment("Rucio WebUI\n{exp}-webui.rucioit.cern.ch")
            rucio_ui = Deployment("Rucio UI\n{exp}-ui.rucioit.cern.ch")
            
        # Rucio daemon services
        with Cluster("Rucio Daemons"):
            judge_pods = ReplicaSet("Judge Services\n(Evaluator/Injector)")
            conveyor_pods = ReplicaSet("Conveyor Services\n(Transfer/Poller)")
            lifecycle_pods = ReplicaSet("Lifecycle Services\n(Reaper/Minos)")
            
        # Support services
        with Cluster("Support Services"):
            pgbouncer = Pod("PGBouncer\nConnection Pool")
            ext_dns = Pod("External DNS")
            monitoring = Prometheus("ServiceMonitor")
            reloader = Pod("Reloader")
            
        # Optional services
        with Cluster("Optional Services"):
            redis = Redis("Redis\nRegistration Cache")
            dev_pod = Ubuntu("Development Pod\nSSH Access")
            reg_tools = Job("Registration Tools\nBatch Jobs")
            
    # Storage elements
    with Cluster("Storage Elements (RSEs)"):
        eos_storage = Storage("EOS Disk Storage\nDISK RSE")
        tape_storage = Storage("CTA Tape Storage\nTAPE RSE")
        
    # Define connections
    users >> internet >> rucio_webui
    users >> internet >> rucio_ui
    users >> internet >> rucio_server
    
    # ArgoCD deployments
    argo_server >> Edge(label="deploy") >> rucio_server
    argo_server >> Edge(label="deploy") >> rucio_auth
    argo_server >> Edge(label="deploy") >> rucio_webui
    argo_server >> Edge(label="deploy") >> rucio_ui
    argo_server >> Edge(label="deploy") >> judge_pods
    argo_server >> Edge(label="deploy") >> conveyor_pods
    
    # Authentication flows
    rucio_auth >> Edge(label="SSO auth") >> cern_sso
    rucio_webui >> Edge(label="SSO auth") >> cern_sso
    
    # Database connections
    rucio_server >> pgbouncer >> Edge(label="pool") >> dbod
    judge_pods >> Edge(label="rules") >> dbod
    
    # Transfer workflows
    conveyor_pods >> Edge(label="submit transfers") >> fts_service
    conveyor_pods >> Edge(label="data movement") >> eos_storage
    conveyor_pods >> Edge(label="data movement") >> tape_storage
    
    # DNS management
    ext_dns >> Edge(label="DNS updates") >> dns_service
    
    # Registration workflow
    reg_tools >> Edge(label="cache") >> redis
    reg_tools >> Edge(label="metadata") >> rucio_server
    
    # Monitoring
    monitoring >> Edge(style="dashed") >> rucio_server
    monitoring >> Edge(style="dashed") >> conveyor_pods
    
    # Auto-reload configuration
    reloader >> Edge(style="dashed", label="watch") >> rucio_server
    reloader >> Edge(style="dashed", label="watch") >> rucio_auth

print("Diagram generated successfully!")
print("Files created:")
print("- rucio_deployment.png")
print("- rucio_deployment_diagram.py")
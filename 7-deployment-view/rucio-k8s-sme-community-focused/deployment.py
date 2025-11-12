#!/usr/bin/env python3
"""
Generic Rucio Deployment Architecture
Community-focused deployment using CNCF technologies and best practices
Removes CERN-specific dependencies for broader adoption
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.k8s.compute import Deployment, Pod, Job, ReplicaSet
from diagrams.k8s.network import Service, Ingress
from diagrams.k8s.storage import PersistentVolume
from diagrams.k8s.rbac import ServiceAccount
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Prometheus
from diagrams.onprem.vcs import Git
from diagrams.onprem.security import Vault
from diagrams.onprem.network import Internet
from diagrams.onprem.client import Users
from diagrams.generic.storage import Storage
from diagrams.k8s.clusterconfig import LimitRange
from diagrams.k8s.others import CRD

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

with Diagram("Generic Rucio Deployment - Stateless Cloud Native", 
             filename="./deployment",
             show=False,
             graph_attr=graph_attr,
             node_attr=node_attr,
             direction="TB"):
    
    users = Users("Research Community\nUsers")
    
    # GitOps Control Plane (Generic)
    with Cluster("GitOps Control Plane"):
        gitops = Git("GitOps Controller\n(ArgoCD/Flux)")
        config_mgmt = Pod("Config Management\n(Kustomize/Helm)")
        gitops >> config_mgmt
        
    # Secret Management (Flexible)
    with Cluster("Secret Management (Choose One)"):
        vault_option = Vault("HashiCorp Vault\n(Option A)")
        k8s_secrets = ServiceAccount("Kubernetes Secrets\n(Option B)")
        external_secrets = CRD("External Secrets\nOperator (Option C)")
        
    # Certificate Management
    with Cluster("Certificate Management"):
        cert_manager = Pod("cert-manager")
        ca_issuer = Pod("CA Issuer\n(Let's Encrypt/Private)")
        cert_manager >> ca_issuer
        
    # Identity Provider (Generic)
    with Cluster("Identity Provider"):
        oidc_provider = ServiceAccount("OIDC Provider\n(Keycloak/Auth0/etc)")
        
    # External Services
    with Cluster("External Services"):
        fts_service = Service("FTS3 / GridFTP\nTransfer Service")
        dns_service = Service("DNS Provider\n(External-DNS)")
        
    # Main Rucio Deployment
    with Cluster("Rucio Cluster"):
        
        # Ingress Layer
        with Cluster("Ingress & Load Balancing"):
            ingress = Ingress("Ingress Controller\n(nginx/traefik)")
            tls_certs = Pod("TLS Certificates\n(auto-renewed)")
            
        # Rucio Services
        with Cluster("Rucio Applications"):
            rucio_server = Deployment("Rucio Server")
            rucio_auth = Deployment("Rucio Auth")
            rucio_webui = Deployment("Rucio WebUI")
            
        # Background Processing
        with Cluster("Rucio Daemons"):
            judge_services = ReplicaSet("Judge Services\n• Rule Engine\n• Evaluator/Injector")
            conveyor_services = ReplicaSet("Conveyor Services\n• Transfer Management\n• Poller/Submitter")
            maintenance_services = ReplicaSet("Maintenance\n• Reaper\n• Undertaker\n• Minos")
            
        # Support Infrastructure
        with Cluster("Infrastructure Services"):
            db_pool = Pod("Connection Pooling\n(PgBouncer)")
            monitoring = Prometheus("Observability Stack\n(Prometheus/Grafana)")
            cache = Redis("Cache Layer\n(Redis/optional)")
            
    # External Managed Services
    with Cluster("External Managed Services"):
        database = PostgreSQL("Managed Database\n(RDS/CloudSQL/Azure DB)")
        
    # Cluster Storage (Stateless)
    with Cluster("Cluster Storage (Ephemeral)"):
        storage_class = PersistentVolume("Ephemeral Storage\n(Logs/Cache only)")
        
    # Storage Elements (Generic)
    with Cluster("Storage Elements (RSEs)"):
        object_storage = Storage("Object Storage\n(S3/Ceph/Swift)")
        posix_storage = Storage("POSIX Storage\n(NFS/CephFS)")
        archive_storage = Storage("Archive Storage\n(Tape/Glacier)")
        
    # User Flow
    users >> Edge(label="HTTPS", color="blue") >> ingress
    ingress >> Edge(color="blue") >> [rucio_webui, rucio_server]
    
    # GitOps Flow
    gitops >> Edge(label="deploy", color="green") >> [rucio_server, rucio_auth, rucio_webui]
    gitops >> Edge(label="deploy", color="green") >> [judge_services, conveyor_services]
    config_mgmt >> Edge(style="dashed", label="config", color="orange") >> gitops
    
    # Certificate Automation
    cert_manager >> Edge(label="auto-renew", color="purple") >> tls_certs
    tls_certs >> Edge(color="purple") >> ingress
    
    # Secret Management (flexible options)
    vault_option >> Edge(style="dashed", label="secrets", color="orange") >> gitops
    k8s_secrets >> Edge(style="dashed", label="secrets", color="orange") >> gitops
    external_secrets >> Edge(style="dashed", label="secrets", color="orange") >> gitops
    
    # Authentication
    rucio_auth >> Edge(label="OIDC", color="purple") >> oidc_provider
    rucio_webui >> Edge(label="OIDC", color="purple") >> oidc_provider
    
    # Database Access
    rucio_server >> db_pool >> Edge(label="SQL", color="red") >> database
    judge_services >> Edge(label="rules & jobs", color="red") >> database
    
    # Data Movement
    conveyor_services >> Edge(label="transfers", color="darkgreen") >> fts_service
    conveyor_services >> Edge(label="data ops", color="darkgreen") >> [object_storage, posix_storage, archive_storage]
    
    # Infrastructure
    monitoring >> Edge(style="dashed", label="metrics", color="gray") >> [rucio_server, judge_services, conveyor_services]
    cache >> Edge(style="dashed", label="cache", color="gray") >> rucio_server

print("Generic Rucio deployment diagram generated!")
print("Key improvements for community adoption:")
print("- Removed CERN-specific dependencies (Vault/AVP)")
print("- Added flexible secret management options") 
print("- Included cert-manager for automated TLS")
print("- Generic OIDC provider support")
print("- Cloud-native storage options")
print("- Standard ingress patterns")
print("- Stateless cluster design with external managed database")
print("- Ephemeral storage only (no persistent state in cluster)")
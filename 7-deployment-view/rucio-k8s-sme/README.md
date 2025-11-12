# Current Rucio Deployment Architecture (CERN-Specific)

## Overview

The current Rucio deployment implements a GitOps-based approach tightly integrated with CERN infrastructure and services.

## Architecture Components

### Control Plane
- **ArgoCD**: GitOps controller managing multi-experiment deployments
- **Vault + AVP**: HashiCorp Vault with ArgoCD Vault Plugin for secrets management
- **CERN GitLab**: Source repository for Helm charts and configurations

### Per-Experiment Clusters
Each experiment (ship, ams02, na62, etc.) receives a dedicated namespace with:

**Core Services:**
- **Rucio Server**: REST API with experiment-specific hostname
- **Rucio Auth**: Authentication service integrated with CERN SSO
- **Rucio WebUI**: Web interface with CERN branding and SSO
- **Rucio Daemons**: Background processing (Judge, Conveyor, Reaper, Minos)

**Infrastructure:**
- **PGBouncer**: Database connection pooling
- **DBOD PostgreSQL**: Managed database per experiment
- **External DNS**: Automated DNS record management for `*.rucioit.cern.ch`

### Storage Integration
- **EOS**: CERN disk storage (DISK RSEs)
- **CTA**: CERN tape archive (TAPE RSEs)
- **FTS3**: File transfer service for data movement

### Networking
- **OpenStack LoadBalancers**: Per-service external access
- **Manual TLS**: Certificates provisioned via Vault
- **CERN SSO**: Authentication for all web interfaces

## Key Characteristics

**Strengths:**
- Fully automated secret management via Vault
- Tight integration with CERN identity and storage systems
- Multi-tenancy with experiment isolation
- Production-proven for multiple physics experiments

**CERN Dependencies:**
- Requires Vault/AVP for secrets
- CERN SSO mandatory for authentication
- EOS/CTA storage infrastructure
- CERN DNS zone management
- Manual certificate lifecycle

## Service Architecture

```
ArgoCD → Helm Charts → Kubernetes Resources:
  - Deployments (application logic)
  - Services (ClusterIP for internal networking)
  - LoadBalancer Services (external access)
  - Secrets (Vault-managed)
```

This architecture serves as the reference implementation for Rucio-IT SME services, optimized for CERN's infrastructure and operational patterns.
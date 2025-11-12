# Rucio Development Environment - Complete Setup

## Overview

This diagram visualizes the complete Rucio development environment as deployed using Docker Compose, providing a comprehensive testing and development platform for the Rucio data management system.

![](./deployment.png)

## Usage

```bash
# Generate the deployment diagram
pip install diagrams
python3 deployment.py
```

## Architecture Components

### Core Services
- **Rucio Server**: Main application container with daemon capabilities
- **Rucio Client**: Development and testing container for manual operations
- **Database Options**: PostgreSQL (default), MySQL 8, or Oracle XE

### Storage Ecosystem (RSEs)
- **XRootD Cluster**: Five XRootD servers providing distributed storage access
- **WebDAV**: HTTP-based file access
- **SSH Transfer**: SFTP/SCP endpoint
- **MinIO S3**: Object storage with S3-compatible API

### Transfer Infrastructure
- **FTS3**: File Transfer Service for reliable data movement
- **MySQL**: Backend database for FTS operations

### Identity & Access Management
- **Keycloak**: Modern OAuth/OIDC provider
- **INDIGO IAM**: Scientific identity and access management
- **IAM Database**: MariaDB backend for authentication services

### Observability Stack
- **Monitoring**: Grafana + InfluxDB + Graphite
- **Logging**: ELK stack (Elasticsearch + Logstash + Kibana)
- **Messaging**: ActiveMQ for FTS3 notifications

### External Metadata Services
- **MongoDB**: NoSQL metadata storage
- **PostgreSQL Meta**: Relational metadata backend
- **Elasticsearch Meta**: Search-based metadata indexing

## Key Features

- **Container-Based Development**: All services run in isolated Docker containers
- **Multiple Protocol Support**: XRootD, WebDAV, SSH/SFTP, S3-compatible storage
- **Flexible Authentication**: OIDC, Scientific Identity, X.509 certificate support
- **Complete Testing Stack**: Full observability and monitoring capabilities
- **Local Development**: All services accessible via localhost port mapping

## Docker Compose Profiles

Use profiles to enable specific service combinations:
- **Default**: Core Rucio services with PostgreSQL
- **Storage**: Adds storage endpoints (FTS, XRootD, WebDAV, SSH, MinIO)
- **IAM**: Enables authentication services (Keycloak, INDIGO IAM)
- **Monitoring**: Activates observability stack (Grafana, ELK)
- **External Metadata**: Additional metadata storage options

---

*This comprehensive development environment mirrors production Rucio deployments while remaining suitable for laptop/workstation development.*
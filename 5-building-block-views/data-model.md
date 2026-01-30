# Data Model

## Overview
Rucio's database schema represents the core domain model for distributed data management, implementing concepts like datasets, replicas, rules and transfer state.

## Entity-Relationship Diagram

![Rucio Database Schema](../images/rucio_erd.png)

*Figure: Complete entity-relationship diagram of the Rucio database schema generated from [source code](https://github.com/rucio/rucio/blob/master/lib/rucio/db/sqla/models.py)*

## Key Entity Groups

**Data Identifiers (DIDs)**
- `dids`: Core table for datasets, containers and files
- `contents`: Hierarchical relationships between DIDs
- Supports namespace organization and metadata attachment

**Replica Management**
- `replicas`: Physical file locations across storage elements
- `rse_protocols`: Storage endpoint configurations
- Tracks replica state lifecycle (available, being_deleted, etc.)

**Replication Rules**
- `rules`: Declarative data placement policies
- `locks`: Reservation mechanism for replica retention
- Enables automatic data distribution and lifetime management

**Transfer Coordination**
- `requests`: Transfer queue entries
- `sources`: Available source replicas for transfers
- Links replication rules to FTS transfer execution

**Accounting & Monitoring**
- `account_limits`: Quota enforcement per RSE
- `rse_usage`: Current storage utilization
- `collection_replicas`: Aggregated dataset statistics

## Design Principles
- Normalized schema for data integrity
- Optimized for high-volume insert/update operations
- Supports multi-VO isolation through account/scope partitioning
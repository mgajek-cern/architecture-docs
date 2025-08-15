Based on the [daemon descriptions](https://rucio.github.io/documentation/started/main_components/daemons) and the [external systems table](../README.md#3-context--scope), here's which external systems each Rucio daemon communicates with:

## Transfer Systems
- **rucio-conveyor-poller** - Polls transfer tools (FTS3, Globus) for status updates via HTTP APIs
- **rucio-conveyor-submitter** - Submits transfer requests to transfer tools (FTS3, Globus) via HTTP APIs

## Storage Systems
- **rucio-auditor** -  Downloads file dumps from storage systems via multiple protocols (HTTP/HTTPS, GFAL2: davs/gsiftp/root/srm, HDFS, object stores with signed URLs)
- **rucio-automatix** - Uploads test data to RSEs via UploadClient for liveness testing
- **rucio-bb8** - Downloads RSE dump files via HTTP/HTTPS and reads storage usage statistics for data rebalancing analysis
- **rucio-reaper** - Deletes expired replicas from storage systems via multiple protocols (HTTP/HTTPS, Globus, GridFTP, etc.) with authentication support
- **rucio-dark-reaper** - Deletes quarantined replicas from storage systems via RSE protocols
- **rucio-storage-consistency-actions** - Processes storage scan results and quarantines dark files or declares missing replicas bad based on storage-consistency-scanner findings

**NOTE:** These daemons handle small files and metadata operations (MB-GB administrative files, KB-MB test files, deletion operations), while transfer tools handle large-scale production data movement (GB-TB physics datasets). Small operations use direct storage protocols; large operations require specialized transfer tools for optimization and reliability.

## Messaging Systems
- **rucio-hermes** - Sends messages to external services (InfluxDB, OpenSearch, ActiveMQ)
- **rucio-cache-consumer** - Consumes cache operation messages from message brokers (ActiveMQ/STOMP) to synchronize volatile replica states
- **rucio-tracer-kronos** - Consumes file access trace messages from ActiveMQ to update replica access times and detect suspicious access patterns
- **rucio-conveyor-receiver** -  Receives real-time notifications from transfer tools via message brokers (STOMP/ActiveMQ)

## Monitoring Systems
- **rucio-hermes** - Publishes messages to ActiveMQ via STOMP protocol

## Email Systems
- **rucio-hermes** - Sends email notifications via SMTP servers 

## Authentication Systems
- **rucio-reaper** - Requests OIDC tokens for authenticated storage access during deletion operations

## Database Systems
All daemons implicitly communicate with database systems since they update Rucio's internal catalog and metadata, but this is through Rucio's internal database layer rather than direct external communication.
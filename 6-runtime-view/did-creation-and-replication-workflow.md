# DID Creation and Replication workflow

## Managed Upload

```mermaid
sequenceDiagram
    participant User
    participant Rucio
    participant RSE1 as RSE (source)
    participant RSE2 as RSE (destination)

    User->>Rucio: rucio upload file
    Rucio->>Rucio: Create DID
    Rucio->>RSE1: Upload file
    Rucio->>Rucio: Register replica (RSE1)

    User->>Rucio: Create replication rule (e.g. copy to RSE2)
    Rucio->>RSE2: Execute transfer
    Rucio->>Rucio: Register replica (RSE2)
```

## Manual Registration

```mermaid
sequenceDiagram
    participant Admin
    participant Rucio
    participant RSE
    participant User

    Admin->>Rucio: rucio did add
    Rucio->>Rucio: Create DID
    Admin->>Rucio: Register existing replica
    Rucio->>RSE: No data movement
    Rucio->>User: Dataset available for download
```

**NOTE:**  
- Each DID represents a single logical file or dataset.  
- One DID can have **multiple replicas** across different RSEs.  
- Replicas are physical copies; the DID abstracts the logical identity.  
- Replication rules create additional replicas without changing the DID.
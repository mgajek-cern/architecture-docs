## Data Identifiers (DIDs)

A Data Identifier (DID) represents the logical identity of a file or dataset
independent of its physical location.

### DID Creation Modes

#### Managed Upload
- Triggered via `rucio upload` (CLI or API)
- Creates:
  - DID
  - Initial replica at target RSE

#### Manual Registration
- Used for externally existing data
- DID created via `rucio did add`
- Replicas registered explicitly
- No data movement performed by Rucio

### External / Pre-existing Data

For data not uploaded through Rucio (e.g. S3 buckets, external archives),
DIDs must be created manually and linked to existing replicas.

## Replicas

A single DID may have multiple replicas across different RSEs.

### Replica Lifecycle
1. Initial upload → replica at source RSE
2. Replication rules trigger transfers
3. Additional replicas created at destination RSEs

Invariant:
- One DID corresponds to one logical file
- Multiple physical replicas may exist simultaneously

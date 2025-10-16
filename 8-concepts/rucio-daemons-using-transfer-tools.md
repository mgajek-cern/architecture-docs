## Rucio Daemons using Transfer Tools (FTS3, Globus)

*Ideally checkout previous concept on [transfer-tool-interface](./transfer-tool-interface.md).*

The source code can be found [here](https://github.com/rucio/rucio/tree/master/lib/rucio/daemons).

---

### 1. **conveyor-submitter**
* **Role:** Submits transfer requests to transfer tools (FTS3, Globus).
* **How it works:** 
  - Fetches transfer requests in `QUEUED` state from the database
  - Retrieves source replicas for each request
  - Uses topology and protocol configuration to determine optimal transfer paths
  - Supports multi-hop transfers between RSEs
  - Groups transfers and submits them via the transfer tool's API (FTS3 REST API or Globus API)
* **Request types handled:** `TRANSFER`, `STAGEIN`, `STAGEOUT` (configurable)
* **Purpose:** Initiates data movement reliably and efficiently, handling job grouping, protocol selection, and submission parameters.
* **Transfer tool support:** FTS3, Globus (configurable via `transfertools` parameter)

---

### 2. **conveyor-poller**
* **Role:** Periodically polls transfer tools to get status updates about ongoing transfers.
* **How it works:**
  - Queries the database for requests in `SUBMITTED` state that are older than a configured threshold (default: 60 seconds)
  - Calls the transfer tool's bulk query API (e.g., FTS3 REST API or Globus API) to fetch current job status
  - Updates the database with transfer states (e.g., running, done, failed)
  - Touches transfer records to prevent redundant polling
* **Purpose:** Keeps Rucio's internal state synchronized with the external transfer system. Provides redundancy in case push notifications are missed.
* **Transfer tool support:** Works with any configured transfer tool (FTS3, Globus, etc.)

---

### 3. **conveyor-receiver** (FTS3-specific)
* **Role:** Listens for real-time completion notifications from FTS3 via ActiveMQ message broker.
* **How it works:**
  - Connects to ActiveMQ brokers using STOMP protocol
  - Subscribes to FTS3 job state messages
  - Processes messages where `job_state != 'ACTIVE'` or for multihop jobs
  - Updates transfer state in the database immediately upon receiving notifications
  - Uses `FTS3CompletionMessageTransferStatusReport` to parse FTS3 messages
* **Purpose:** Provides near-instant updates to Rucio when FTS3 transfers complete or fail, reducing latency compared to polling.
* **Important:** This daemon is **FTS3-specific** and does **NOT** work with Globus. It requires ActiveMQ configuration (`messaging-fts3` section).

---

### 4. **conveyor-finisher**
* **Role:** Processes completed transfer requests and updates the replica catalog.
* **How it works:**
  - Polls the database for requests in terminal states: `DONE`, `FAILED`, `LOST`, `SUBMISSION_FAILED`, `NO_SOURCES`, `ONLY_TAPE_SOURCES`, `MISMATCH_SCHEME`
  - Also handles stuck requests in `SUBMITTING` state (older than 120 minutes)
  - Updates replica states to `AVAILABLE` or `UNAVAILABLE`
  - Implements retry logic with exponential backoff
  - Archives completed requests
  - Handles suspicious file patterns and declares bad replicas
  - For non-deterministic RSEs (tape), extracts and stores replica paths
* **Request types handled:** `TRANSFER`, `STAGEIN`, `STAGEOUT`
* **Purpose:** Final processing of all completed transfers regardless of transfer tool. Updates the replica catalog, handles retries, and cleans up request records.
* **Transfer tool support:** Works with **all transfer tools** (FTS3, Globus, etc.) since it operates at the database level, not via transfer tool APIs.

---

### 5. **conveyor-stager**
* **Role:** Specialized submitter for tape staging operations (STAGEIN requests).
* **How it works:**
  - Wraps the `conveyor-submitter` functionality
  - Hardcoded to handle only `RequestType.STAGEIN` requests
  - Uses FTS3 as the transfer tool (currently only supports FTS3)
  - Sets `default_lifetime=-1` for staging jobs (no automatic cleanup)
  - Brings files from tape to disk cache before actual transfers
* **Purpose:** Manages the staging of files from tape storage systems to disk, making them available for subsequent transfers. This is necessary because tape systems require explicit staging operations before files can be accessed.
* **Transfer tool support:** Currently FTS3 only (via SRM protocol for tape operations)

---

## Summary of Operation Flow with Transfer Tools

```
┌─────────────────────────────────────────────────────────────────┐
│                        Transfer Workflow                         │
└─────────────────────────────────────────────────────────────────┘

1. Request Creation (by Rucio core/rules)
   ↓
2. **conveyor-stager** (if tape source)
   - Submits STAGEIN requests to bring files from tape to disk
   ↓
3. **conveyor-submitter**
   - Fetches QUEUED requests from database
   - Determines transfer paths and protocols
   - Submits to FTS3/Globus APIs
   - Requests transition to SUBMITTED state
   ↓
4. **Status Monitoring** (parallel paths):
   
   Path A (Push - FTS3 only):
   **conveyor-receiver** 
   - Receives ActiveMQ messages from FTS3
   - Updates states immediately
   
   Path B (Pull - all transfer tools):
   **conveyor-poller**
   - Polls FTS3/Globus APIs periodically
   - Updates states from API responses
   ↓
5. **conveyor-finisher**
   - Processes terminal states (DONE/FAILED)
   - Updates replica catalog (AVAILABLE/UNAVAILABLE)
   - Implements retry logic
   - Archives completed requests
```

---

## Why use Transfer Tools?

* Transfer tools like **FTS3** and **Globus** specialize in reliable, high-performance, large-scale data movement
* They provide:
  - Optimized handling for retries, bandwidth management, and priorities
  - Multi-protocol support (GridFTP, WebDAV, XRootD, S3, etc.)
  - Third-party copy (TPC) capabilities for direct endpoint-to-endpoint transfers
  - Built-in monitoring and logging
  - Queue management and job scheduling
* Rucio leverages these tools for the actual data transfer mechanics, focusing instead on:
  - High-level data management policies and rules
  - Replica catalog consistency
  - Multi-hop transfer orchestration
  - Storage system abstraction

---

## Key Implementation Notes

**Daemon Naming Convention:**
- Executable names: `rucio-conveyor-submitter`, `rucio-conveyor-poller`, etc.
- Internal daemon names (in code): `conveyor-submitter`, `conveyor-poller`, etc.

**Transfer Tool Configuration:**
- Configurable via `conveyor` section in `rucio.cfg`
- `transfertool` parameter supports: `fts3`, `globus`
- `filter_transfertool` can restrict which transfer tool a daemon instance handles

**State Transitions:**
```
QUEUED → [submitter] → SUBMITTED → [poller/receiver] → DONE/FAILED → [finisher] → AVAILABLE/UNAVAILABLE
```

**Complementary Nature:**
- **receiver** (push) and **poller** (pull) provide redundancy for status updates
- **finisher** is the final processing step regardless of how the status was obtained
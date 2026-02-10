# TransferTool Interface (Rucio)

* **Purpose:**
  Defines a standard interface for different *transfer tools* (external systems/services) that manage data transfers between storage endpoints (RSEs).

  The source code to refer to can be found [here](https://github.com/rucio/rucio/tree/master/lib/rucio/transfertool).

  Rucio acts as the **control plane**, deciding *what* data should be transferred, *where*, and *when*.
  Transfer tools implement the **data plane**, executing the actual byte-level movement between storage endpoints.

* **Key Methods:**

  * `submission_builder_for_path()`: Analyze if a transfer path can be handled by this tool and prepare the submission builder.
  * `group_into_submit_jobs()`: Group transfers for bulk submission.
  * `submit()`: Submit transfer requests to the external transfer service.
  * `bulk_query()`: Query the status of multiple transfers.
  * `cancel()`: Cancel active transfers.
  * `update_priority()`: Adjust the priority of submitted transfers.

* **Common Properties:**

  * Must declare supported protocols and required RSE attributes.
  * Can decide if it can perform a transfer between two given RSEs.

---

### Implementations

#### 1. **FTS3 (File Transfer Service v3)**

* **Role:** The primary, high-performance grid transfer service used in WLCG and other distributed infrastructures.
* **Characteristics:**

  * Supports multi-hop and multi-source transfers.
  * Uses HTTP/REST API to submit and monitor transfers.
  * Handles advanced features like checksum verification, bring-online for tape, token-based authentication.
  * Highly integrated with Rucio’s needs and workflow.

#### 2. **BitTorrent**

* **Role:** P2P file distribution protocol adapted for large-scale data transfers in distributed systems.
* **Characteristics:**

  * Allows efficient replication by distributing pieces of data across multiple peers.
  * Used for distributing popular datasets with minimal load on central servers.
  * Less about direct grid RSE-to-RSE transfers, more about efficient bulk distribution.

#### 3. **Globus**

* **Role:** Commercial/enterprise data transfer platform offering robust, secure, and optimized file transfers.
* **Characteristics:**

  * Supports high-performance transfers with encryption, retry, and fault tolerance.
  * Can be integrated as a backend transfer tool, mainly where Globus endpoints are used.
  * Supports token-based authentication and detailed monitoring.

---

### Summary

* **All three implement the same interface** so Rucio can **abstract the transfer layer**, allowing interchangeable backends.
* **FTS3 is the "default" grid-native transfer tool**, ideal for complex grid workflows.
* **BitTorrent suits bulk, large-scale data replication scenarios** with P2P characteristics.
* **Globus fits environments needing commercial-grade transfers or integration with Globus-managed storage endpoints.**
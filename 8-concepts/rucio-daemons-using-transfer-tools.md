Ideally checkout previous concept on [transfer-tool-interface](./transfer-tool-interface.md).

---

### Rucio Daemons using Transfer Tools (FTS3, Globus)

The source code to refer to can be found [here](https://github.com/rucio/rucio/tree/master/lib/rucio/daemons).

#### 1. **rucio-conveyor-submitter**

* **Role:** Submits transfer requests to transfer tools.
* **How it uses FTS3:** Takes a batch of file transfer jobs and submits them via FTS3’s HTTP API to start moving data between storage endpoints.
* **Purpose:** Initiates transfers reliably and efficiently, handling retries and job parameters.

#### 2. **rucio-conveyor-poller**

* **Role:** Periodically polls transfer tools to get status updates about ongoing transfers.
* **How it uses FTS3:** Queries FTS3’s REST API to fetch the current status of submitted transfer jobs (e.g., running, done, failed).
* **Purpose:** Keeps Rucio’s internal state up to date by syncing with the external transfer system status.

#### 3. **rucio-conveyor-receiver**

* **Role:** Listens for real-time notifications from transfer tools via messaging brokers.
* **How it uses FTS3:** Subscribes to messages sent by FTS3 or Globus about transfer job completions or failures.
* **Purpose:** Provides near-instant updates to Rucio without waiting for the poller cycle, improving responsiveness.

#### 4. **rucio-conveyor-stager** (less directly related to transfer tools)

* **Role:** Prepares or stages data at storage endpoints, often before or after transfers.
* **Relation to FTS3:** May work alongside transfer tools but focuses on storage-level operations rather than submitting or monitoring transfers.

---

### Summary of Operation Flow with Transfer Tools:

1. **Submitter** sends transfer requests to FTS3 or Globus.
2. **Poller** regularly checks the status of these transfers via their APIs.
3. **Receiver** listens for immediate event notifications pushed from the transfer tools.
4. **Stager** ensures data is properly staged/prepared on storage endpoints as needed.

---

### Why use Transfer Tools?

* Transfer tools like **FTS3** and **Globus** specialize in reliable, high-performance, large-scale data movement.
* They provide optimized handling for retries, bandwidth, priorities, and multi-protocol support.
* Rucio leverages these tools instead of implementing data transfer itself, focusing on orchestration and catalog management.
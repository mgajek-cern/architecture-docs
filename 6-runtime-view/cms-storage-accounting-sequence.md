# CMS storage accounting sequence

Runtime view supporting [ADR-009](../9-adrs/adr-009-cms-storage-accounting-via-rucio.md) and [concept](../8-concepts/cms-storage-accounting.md).

## dumper-fed loop (Rucio-internal, periodic)

```mermaid
sequenceDiagram
    participant D as rucio-dumper (or storage-side dump tool)
    participant S as Storage Site
    participant A as rucio-auditor
    participant DB as Rucio DB

    S->>D: storage publishes file inventory
    D->>DB: dump file (per RSE)
    A->>DB: read dump + logical view
    A->>DB: write quarantined_replicas / drift flags
```

## CMS query (on-demand)

```mermaid
sequenceDiagram
    participant CMS as CRMS (RUEIT)
    participant API as Rucio REST API
    participant DB as Rucio DB
    participant CTPM as CTPM
    participant CAR as CAR

    CMS->>API: GET /accounts/{acct}/usage  (or /rses/{rse}/usage)
    API->>DB: aggregate from account_counter / rse_counter
    DB-->>API: usage rows (bytes, files, last_reconciled_at)
    API-->>CMS: reconciled usage feed
    CMS->>CTPM: translate usage → credits
    CTPM->>CAR: debit project credits
```

## Drift handling (when Auditor finds mismatch)

```mermaid
sequenceDiagram
    participant A as Auditor
    participant DB as Rucio DB
    participant CMS as CRMS

    A->>DB: write drift event (dark file / orphan)
    Note over DB: rucio-hermes emits event<br/>(if subscribed)
    DB->>CMS: drift notification (optional)
    Note over CMS: policy decision —<br/>bill on logical or physical?
```

## What this maps to in the C4 view

The CRMS box contains CTPM, CDPM, CAR, RUEIT, API. The arrows above land on **RUEIT** (consumes Rucio data) and **CAR** (records the resulting credit movements). Rucio sits outside the CRMS boundary, in the position the C4 diagram leaves to "Compute / Data holding" peers.
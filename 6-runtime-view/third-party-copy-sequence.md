# Third-Party Copy Sequence

Refer to [Rucio Tokens Documentation](https://rucio.cern.ch/documentation/files/Rucio_Tokens_v0.1.pdf). 

Optionally, you may also refer to the following concepts for additional context: [Transfer Tool Interface](../8-concepts/transfer-tool-interface.md), [WLCG Tokens](../8-concepts/wlcg-tokens.md), [Rucio Daemons Using Transfer Tools](../8-concepts/rucio-daemons-using-transfer-tools.md), and [Storage Service Endpoints](../8-concepts/storage-service-endpoints.md). 

## Overview

Third-party copy enables direct data transfer between storage systems without data flowing through intermediate services like FTS. The workflow involves token-based authentication where Rucio orchestrates token acquisition from a centralized Identity Provider, and storage systems may validate tokens locally for optimal performance.

## Key Components

- **Rucio**: Orchestrates the transfer workflow and manages token requests
- **Identity Provider (IdP)**: Issues OIDC/JWT tokens for authentication
- **FTS**: Transfer service that coordinates the actual copy operation
- **Storage Systems**: Source and destination endpoints that validate tokens and perform transfers

## Token Flow

1. **Rucio requests all tokens from IdP** using its own service token (r⃝)
2. **Storage systems only validate tokens** - they don't issue them
3. **Three separate tokens**: FTS auth (f⃝), source read (s⃝), destination write (d⃝)
4. **All tokens are OIDC/JWT tokens** from the Identity Provider

## Validation Methods

- **Offline validation**: Storage systems validate JWT signatures and claims locally using cached public keys
- **Online validation**: Storage queries IdP introspection endpoint for each token - creates performance bottlenecks

```mermaid
sequenceDiagram
    participant U as User
    participant R as Rucio
    participant I as IdP
    participant F as FTS
    participant S1 as Source Storage
    participant S2 as Destination Storage
    
    U->>R: Data transfer rule
    R->>I: OIDC auth (using Rucio's token r⃝)
    I-->>R: JWT + WLCG claims
    
    Note over R: Rucio requests tokens for both RSEs
    R->>I: Request source token (using r⃝)
    I-->>R: Source token (s⃝)
    
    R->>I: Request destination token (using r⃝)
    I-->>R: Destination token (d⃝)
    
    R->>I: Request FTS token (using r⃝)
    I-->>R: FTS token (f⃝)
    
    R->>F: Submit transfer job + f⃝ + s⃝ + d⃝
    
    Note over F,S2: Third-party copy via WebDAV COPY
    F->>S2: COPY request + d⃝ + TransferHeaderAuth: s⃝
    
    Note over S2: Token validation approach
    alt Online validation
        S2->>I: Introspect d⃝
        I-->>S2: Valid/Invalid
    else Offline validation
        Note over S2: Validate JWT signature & claims locally
    end
    
    S2->>S1: GET request + s⃝
    
    Note over S1: Token validation approach  
    alt Online validation
        S1->>I: Introspect s⃝
        I-->>S1: Valid/Invalid
    else Offline validation
        Note over S1: Validate JWT signature & claims locally
    end
    
    S1-->>S2: Data transfer
    S2-->>F: Transfer complete
    F-->>R: Status
    R-->>U: Result
```

## Third-Party Copy Mechanism

Third-party copy enables direct data transfer between storage systems using multiple protocol implementations:

### Protocol-Specific TPC Implementations

**HTTP-TPC (WebDAV)**:
1. **FTS initiates**: Sends COPY request to destination storage with destination token (d⃝)
2. **Token propagation**: Includes source token (s⃝) in `TransferHeaderAuthorization` header
3. **Direct transfer**: Destination storage validates both tokens and directly retrieves data from source

**Other TPC Protocol Implementations** (not depicted in the sequence diagram):

**GridFTP-TPC**: Enables direct transfers between GridFTP endpoints using parallel data streams. FTS coordinates the operation while data flows directly between storage systems, delivering high throughput for large scientific datasets.

**XRootD-TPC**: Provides native third-party copying within the XRootD ecosystem using the `root://` protocol. This approach minimizes latency and eliminates intermediate buffering, making it well-suited for High Energy Physics applications requiring rapid data access.

### Universal TPC Advantages

Regardless of the underlying protocol, third-party copy mechanisms deliver consistent benefits:

- **Reduced network overhead** by eliminating intermediate data hops through transfer services
- **Improved throughput** through direct storage-to-storage communication paths  
- **Enhanced infrastructure scalability** by reducing bottlenecks at transfer coordination points
- **Consistent security model** maintaining token-based authentication across all protocols

The availability of multiple TPC implementations allows the scientific computing infrastructure to match transfer protocols with specific storage technologies and performance requirements, while preserving the fundamental efficiency gains of direct endpoint communication.
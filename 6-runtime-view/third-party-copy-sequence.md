# Third-Party Copy Sequence

Refer to [Rucio Tokens Documentation](https://rucio.cern.ch/documentation/files/Rucio_Tokens_v0.1.pdf). 

Optionally, you may also refer to the following concepts for additional context: [Transfer Tool Interface](../8-concepts/transfer-tool-interface.md), [WLCG Tokens](../8-concepts/wlcg-tokens.md), [Rucio Daemons Using Transfer Tools](../8-concepts/rucio-daemons-using-transfer-tools.md), and [Storage Service Endpoints](../8-concepts/storage-service-endpoints.md). 

## Overview

Third-party copy enables direct data transfer between storage systems while FTS coordinates the transfer without data flowing through FTS itself. The workflow involves token-based authentication where Rucio orchestrates token acquisition from a centralized Identity Provider, and storage systems may validate tokens locally for optimal performance.

Third-Party Copy (TPC) sequence:

```mermaid
sequenceDiagram
   participant U as User
   participant R as Rucio
   participant I as IAM System
   participant F as FTS
   participant S1 as Source Storage
   participant S2 as Destination Storage
  
   U->>R: Data transfer rule
   
   Note over R: Check Rucio authentication token cache
   alt Valid Rucio token in cache
       Note over R: Reuse cached authentication token
   else No valid token or expired
       R->>I: OIDC auth (using Rucio's token r)
       I-->>R: JWT + cache with TTL
   end
  
   Note over R: Check RSE token cache for both source and destination
   alt Valid source token in cache
       Note over R: Reuse cached source token (s)
   else Request new source token
       R->>I: Request source token (using r)
       I-->>R: Source token (s) + cache with TTL
   end
   
   alt Valid destination token in cache
       Note over R: Reuse cached destination token (d)
   else Request new destination token
       R->>I: Request destination token (using r)
       I-->>R: Destination token (d) + cache with TTL
   end
   
   Note over R: Check FTS token cache
   alt Valid FTS token in cache
       Note over R: Reuse cached FTS token (f)
   else Request new FTS token
       R->>I: Request FTS token (using r)
       I-->>R: FTS token (f) + cache with TTL
   end
  
   R->>F: Submit transfer job + f + s + d
   
   Note over F: Token refresh during long transfers
   loop Periodic token refresh (every few hours)
       F->>I: Refresh source token (s) if needed
       I-->>F: Refreshed source token
       F->>I: Refresh destination token (d) if needed  
       I-->>F: Refreshed destination token
   end
   
   Note over F: Pre-transfer validation
   F->>S1: Check source file exists + s
   S1->>I: Introspect s (introspection-based validation)
   I-->>S1: Valid/Invalid
   S1-->>F: File exists confirmation
   
   F->>S2: Check destination path + d  
   S2->>I: Introspect d (introspection-based validation)
   I-->>S2: Valid/Invalid
   S2-->>F: Path status
   
   Note over F: Optional cleanup if destination exists
   alt Destination exists and overwrite enabled
       F->>S2: Delete existing file + d
       S2-->>F: Deletion complete
   end
   
   Note over F,S2: Third-party copy via WebDAV COPY
   F->>S2: COPY request + d + TransferHeaderAuth: s
  
   Note over S2: Destination storage token validation
   alt Introspection-based validation
       S2->>I: Introspect d
       I-->>S2: Valid/Invalid + cache validation result
   else Offline validation
       Note over S2: Validate JWT signature & claims locally
   end
  
   S2->>S1: GET request + s
  
   Note over S1: Source storage token validation 
   alt Introspection-based validation
       S1->>I: Introspect s
       I-->>S1: Valid/Invalid + cache validation result
   else Offline validation
       Note over S1: Validate JWT signature & claims locally
   end
  
   S1-->>S2: Data transfer (direct storage-to-storage)
   
   Note over F: Post-transfer validation
   F->>S2: Verify file integrity + d
   S2-->>F: Checksum/size confirmation
   
   S2-->>F: Transfer complete
   F-->>R: Transfer status + metrics
   R-->>U: Result with transfer details
```

Introspection-based validation sequence:

```mermaid
sequenceDiagram
    participant S as Storage System
    participant I as IAM/IdP
    
    Note over S: Receive request with JWT token
    S->>I: POST /oauth2/introspect
    Note over S,I: Content: token=eyJhbGciOiJSUzI1NiIs...
    Note over S,I: Headers: Authorization: Bearer <client_credentials>
    
    I->>I: Validate token signature & claims
    I->>I: Check expiration, audience, scope
    I->>I: Verify token not revoked
    
    I-->>S: HTTP 200 OK
    Note over S,I: {"active": true, "scope": "storage.read", "sub": "user123"}
    
    alt Token invalid/expired
        I-->>S: HTTP 200 OK  
        Note over S,I: {"active": false}
    else IAM unavailable
        I-->>S: HTTP 500/503 Error
        Note over S: Fallback to offline validation or reject
    end
    
    Note over S: Cache result for X minutes (optional)
    S->>S: Allow/deny storage operation
```

Offline validation sequence:

```mermaid
sequenceDiagram
    participant S as Storage System
    participant Cache as Local Cache
    participant I as IAM/IdP (for keys only)
    
    Note over S: Receive request with JWT token
    S->>Cache: Check cached public keys
    
    alt Public keys cached and valid
        Cache-->>S: RSA/ECDSA public keys
    else Keys expired or missing
        S->>I: GET /.well-known/jwks.json
        I-->>S: Public keys (JWK Set)
        S->>Cache: Cache keys for 24h
    end
    
    S->>S: Parse JWT header/payload
    S->>S: Verify signature with public key
    S->>S: Check expiration (exp claim)
    S->>S: Validate audience (aud claim)
    S->>S: Check scope permissions
    
    alt Token valid
        Note over S: Allow storage operation
    else Token invalid/expired
        Note over S: Reject request
    end
```

## Key Components

- **Rucio**: Orchestrates the transfer workflow and manages token requests
- **Identity Provider (IdP)**: Issues OIDC/JWT tokens for authentication
- **FTS**: Transfer service that coordinates the actual copy operation
- **Storage Systems**: Source and destination endpoints that validate tokens and perform transfers

## Token Flow

1. **Rucio requests all tokens from IdP** using its own service token (r⃝) with multi-level caching
2. **Storage systems only validate tokens** - they don't issue them, but may cache validation results
3. **Three separate tokens**: FTS auth (f⃝), source read (s⃝), destination write (d⃝)
4. **All tokens are OIDC/JWT tokens** from the Identity Provider with configurable TTL

## Validation Methods

- **Offline validation**: Storage systems validate JWT signatures and claims locally using cached public keys - fastest performance
- **Introspection-based validation**: Storage queries IdP introspection endpoint for each token - creates performance bottlenecks but enables real-time revocation
- **Validation result caching**: Storage endpoints may cache validation outcomes to reduce repeated IdP queries

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

### Caching Strategy

**Multi-level token caching** reduces Identity Provider load and improves performance across the federated infrastructure:

- **Rucio Server Cache**: Stores RSE and FTS tokens with TTL-based expiration
- **Client-side Cache**: Rucio CLI and API clients maintain local token stores  
- **Storage Endpoint Cache**: Validation results cached to minimize IdP introspection calls
- **FTS Token Management**: Automatic refresh of long-lived transfer tokens

**Trade-offs**: Aggressive caching improves performance but may delay permission revocation propagation. Cache TTL configuration balances responsiveness with system load.

## Multi-IdP variant

### Status quo: single-IdP submission

Rucio fetches both tokens from one issuer. FTS3 already keys per-token by issuer, so no FTS3-side change is needed for this flow.

```mermaid
sequenceDiagram
    participant R as Rucio
    participant A as IdP A
    participant FS as FTS submit
    participant FT as fts_token
    participant UC as url-copy

    R->>A: request_token(aud=src, scope=storage.read, offline_access)
    A-->>R: access_token (iss=A)
    R->>A: request_token(aud=dst, scope=storage.modify, offline_access)
    A-->>R: access_token (iss=A)
    R->>FS: POST /jobs (source_tokens[], destination_tokens[])
    FS->>FS: persist t_token rows (issuer=A)
    FS->>FT: schedule exchange & refresh
    FT->>A: RFC 8693 token exchange (per token's iss)
    FS->>UC: spawn with src/dst token_id
    UC-->>UC: gfal2 TPC: src→dst with both bearer tokens
```

### Desired state: multi-IdP submission

Rucio resolves the issuer **per RSE** (`RseAttr.OIDC_ISSUER`). Source and destination tokens may carry different `iss` claims. FTS3 schema is unchanged.

```mermaid
sequenceDiagram
    participant R as Rucio
    participant A as IdP A
    participant B as IdP B
    participant FT as fts_token
    participant UC as url-copy

    R->>A: request_token(aud=src, scope=storage.read), issuer=A
    A-->>R: access_token (iss=A)
    R->>B: request_token(aud=dst, scope=storage.modify), issuer=B
    B-->>R: access_token (iss=B)
    R->>FT: POST /jobs (tokens carry distinct iss claims)
    FT->>FT: persist two t_token rows (issuer A and B)
    FT->>A: exchange src token at IdP A
    FT->>B: exchange dst token at IdP B
    FT->>UC: spawn url-copy
    UC-->>UC: gfal2 TPC: src bearer (iss=A), dst bearer (iss=B)
```

### What changes, what doesn't

| Component       | Change                                                                    |
| --------------- | ------------------------------------------------------------------------- |
| Rucio RSE model | New attribute `RseAttr.OIDC_ISSUER`                                       |
| Rucio OIDC core | `request_token(audience, scope, issuer=...)` dispatches per-IdP config    |
| FTS3 schema     | None (`t_token.issuer`, `t_token_provider` already exist)                 |
| FTS3 executors  | Verify no IAM-flavored assumptions block non-IAM IdPs (tracked as a risk) |
| `url-copy`      | None                                                                      |

See [`concept-001-wp2-004-multi-idp-third-party-copy.md`](../8-concepts/concept-001-wp2-004-multi-idp-third-party-copy.md) for the full design.
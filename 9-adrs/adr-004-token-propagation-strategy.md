---
# Configuration for the Jekyll template "Just the Docs"
parent: Decisions
nav_order: 104
title: Token Propagation Strategy for Service-to-Service Communication

status: "proposed"
date: 2025-11-27
decision-makers: "Architecture Team, Security Team"
consulted: "Platform Engineering Team, Identity Management Team"
informed: "Development Teams, Operations Team"
---
<!-- markdownlint-disable-next-line MD025 -->

# Token Propagation Strategy for Service-to-Service Communication

## Context and Problem Statement

In our Zero Trust Architecture, services must authenticate and authorize every request, including service-to-service communication. When User A calls Service 1, which then calls Service 2, which calls Service 3, we need to determine how identity and authorization context flows through the chain. We need a strategy that maintains user context for authorization decisions while ensuring security, auditability, and performance in distributed service calls.

Relates to:
- [ADR on Zero Trust Architecture with API Gateway and Sidecar Authorization](./adr-002-zero-trust-architecture-with-api-gateway.md)

## Decision Drivers

* Maintain user identity context throughout service call chains for fine-grained authorization
* Minimize token exposure and blast radius if tokens are compromised
* Enable proper audit trails linking all service calls back to original user
* Support both user-initiated requests and automated service-to-service calls
* Ensure compatibility with existing OAuth2/OIDC infrastructure
* Minimize token validation overhead in service call chains
* Support token revocation and short-lived credentials
* Enable services to make context-aware authorization decisions

## Considered Options

* Direct token passthrough - forward original user tokens
* Token exchange - exchange user tokens for service-scoped tokens
* User context propagation with service identity - extract user claims, use service mTLS

## Decision Outcome

Chosen option: "Direct token passthrough - forward original user tokens", because it provides the best balance of simplicity, performance, and functionality while maintaining user context for authorization decisions. This approach is widely used by production systems at scale (Netflix, Uber, Airbnb) and avoids the operational complexity of token exchange infrastructure.

**Production Reality**: This pattern is used by companies at scale including Netflix, Uber, and Airbnb. The security risk is mitigated through short-lived tokens (15-30 minutes), proper JWT validation at each service, and mTLS for service-to-service communication. Token exchange adds significant operational complexity that most organizations avoid unless specifically required for regulatory compliance.

### Consequences

* Good, because simplest implementation with minimal latency overhead (<1ms token validation)
* Good, because preserves complete user context for authorization and audit purposes
* Good, because no additional infrastructure required for token management
* Good, because proven at scale by Netflix, Uber, Airbnb production systems
* Good, because works with existing OAuth2/OIDC flows without modification
* Good, because reduces operational complexity and potential points of failure
* Good, because faster development velocity without token exchange complexity
* Bad, because user token exposed to all downstream services in call chain
* Bad, because larger blast radius if any service in chain is compromised
* Bad, because original token may have broader scope than needed for downstream operations

### Confirmation

Implementation compliance will be confirmed through:
* Security audits verifying token validation in 100% of services throughout call chains
* Performance testing showing token validation latency <5ms for 95% of requests
* Integration testing confirming user context preservation through service call chains
* Audit log verification showing complete traceability from user to all service calls
* Token security validation ensuring proper JWT validation and short token lifetimes
* Monitoring dashboards showing token validation success rates and performance

## Pros and Cons of the Options

### Direct token passthrough - forward original user tokens

Services forward the original user access token to downstream services without modification.

```
User Token ──▶ Service A ──▶ Service B ──▶ Service C
   (same token propagated through entire chain)
```

* Good, because simplest implementation with minimal latency overhead (<1ms per service)
* Good, because preserves complete user context and permissions for authorization
* Good, because no additional infrastructure required for token management
* Good, because works with existing OAuth2/OIDC flows without modification
* Good, because proven at scale by Netflix, Uber, Airbnb production systems
* Good, because faster development velocity and reduced operational complexity
* Good, because single token validation pattern across all services
* Good, because complete audit trail with original user context preserved
* Neutral, because security mitigated by short token lifetimes (15-30 minutes) and mTLS
* Bad, because user token exposed to all downstream services in call chain
* Bad, because larger blast radius if any service in chain is compromised

### User context propagation with service identity

Services extract user context from tokens and propagate claims/headers while using service-specific mTLS certificates for authentication.

```
User Token ──▶ Service A ──extract user context──▶ Service B (mTLS + headers)
                   │                                      │
              Service Cert                          Service Cert
```

* Good, because service-to-service communication uses strong mTLS authentication
* Good, because user tokens are not exposed to downstream services
* Good, because user context preserved through custom headers or claims
* Good, because supports complex authorization scenarios with service and user context
* Good, because enables fine-grained service identity management
* Neutral, because requires PKI infrastructure for service certificates
* Bad, because custom implementation without standard protocols
* Bad, because difficult to ensure user context integrity and prevent spoofing
* Bad, because complex audit trail reconstruction from headers and certificates
* Bad, because inconsistent with OAuth2/OIDC ecosystems and tooling

### Token exchange - exchange user tokens for service-scoped tokens

Services exchange user tokens for new tokens scoped for specific downstream service interactions using OAuth2 Token Exchange (RFC 8693).

```
User Token ──▶ Service A ──token exchange──▶ Scoped Token ──▶ Service B
                   │                              │
            Token Exchange Service        (limited scope/lifetime)
```

* Good, because minimizes token scope and exposure (principle of least privilege)
* Good, because supports short-lived tokens reducing compromise impact
* Good, because follows OAuth2 Token Exchange standard (RFC 8693)
* Good, because enables different permission scopes for each service interaction
* Good, because maintains user context in exchanged token claims
* Good, because supports impersonation delegation patterns securely
* Good, because integrates well with existing OAuth2/OIDC infrastructure
* Good, because enables centralized token policies and audit logging
* Neutral, because requires token exchange service infrastructure
* Bad, because adds latency for token exchange operation (network call)
* Bad, because more complex implementation than direct passthrough
* Bad, because requires careful design of token scopes and exchange policies

## More Information

**Token Exchange Implementation (RFC 8693):**
```
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token={user_access_token}
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=service-b.internal
&scope=read:documents write:logs
&requested_token_type=urn:ietf:params:oauth:token-type:access_token
```

**Service Call Flow:**
```
1. User calls Service A with original access token
2. Service A validates user token locally (JWT verification)
3. Service A exchanges user token for Service B scoped token
4. Service A calls Service B with scoped token
5. Service B validates scoped token and processes request
6. Service B may exchange for Service C scoped token if needed
```

**Token Scoping Strategy:**
- **Audience**: Specific target service identifier
- **Scope**: Minimal permissions required for the operation
- **Subject**: Original user identity preserved in sub claim
- **Lifetime**: Short-lived (5-15 minutes) for security
- **Issuer**: Token exchange service identifier

**Exchange Token Claims:**
```json
{
  "iss": "https://token-exchange.internal",
  "aud": "service-b.internal", 
  "sub": "original-user-id",
  "azp": "service-a",
  "scope": "read:documents",
  "act": {
    "sub": "service-a"
  },
  "exp": 1640995200,
  "iat": 1640994300
}
```

**Security Considerations:**
- **Token Validation**: All services must validate tokens cryptographically
- **Scope Restriction**: Exchanged tokens have minimal required permissions
- **Audit Trail**: Complete logging of user → service A → service B chains
- **Token Rotation**: Exchanged tokens are single-use or very short-lived
- **Revocation**: User token revocation invalidates all exchanged tokens

**Performance Optimizations:**
- **Token Caching**: Cache exchanged tokens for repeated calls (with TTL)
- **Batch Exchange**: Exchange multiple tokens in single request where possible
- **Async Exchange**: Pre-exchange tokens for predictable call patterns
- **Local Validation**: Services validate tokens locally without calling exchange service

**Infrastructure Requirements:**
- **Token Exchange Service**: OAuth2-compliant service supporting RFC 8693
- **Key Management**: Secure distribution of signing keys for token validation
- **Service Registry**: Mapping services to allowed scopes and audiences
- **Monitoring**: Token exchange latency, success rates, and security metrics

**Rollout Strategy:**
1. **Phase 1**: Deploy token exchange service infrastructure
2. **Phase 2**: Implement token exchange in critical service call paths
3. **Phase 3**: Replace direct token passthrough patterns across all services
4. **Phase 4**: Implement advanced features (caching, batching, async)
5. **Phase 5**: Security audit and penetration testing

**Supported Token Exchange Implementations:**
- **Keycloak**: Built-in RFC 8693 support with configurable policies
- **Auth0**: Token exchange via custom rules and actions
- **Okta**: Token exchange with Okta Authorization Server
- **Custom**: Implementation using JWT libraries and OAuth2 frameworks

**Performance Targets:**
- **Exchange Latency**: <50ms for 95% of exchange operations
- **Cache Hit Rate**: >80% for repeated service call patterns
- **Availability**: 99.9% uptime for token exchange service
- **Throughput**: 10,000+ exchanges per second per exchange service instance

This decision should be re-evaluated if token exchange latency exceeds acceptable limits, if the operational complexity significantly impacts development velocity, or if security requirements change to mandate different token propagation patterns.
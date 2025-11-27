---
# Configuration for the Jekyll template "Just the Docs"
parent: Decisions
nav_order: 102
title: Zero Trust Architecture with API Gateway

status: "proposed"
date: 2025-11-27
decision-makers: "Architecture Team"
consulted: "Security Team, Platform Engineering Team"
informed: "Development Teams, Operations Team"
---
<!-- markdownlint-disable-next-line MD025 -->

# Zero Trust Architecture with API Gateway and Sidecar Authorization

## Context and Problem Statement

Current distributed systems rely on perimeter-based security models that assume trust within internal networks. This approach becomes inadequate for modern microservices architectures where services need fine-grained access control for both **north-south traffic** (external clients to services) and **east-west traffic** (service-to-service communication) regardless of network location. We need to implement a security model that validates every request and enforces policies consistently across all services while maintaining performance and operational simplicity.

**Scope Note**: This ADR focuses on application-layer zero trust architecture using API gateways for north-south traffic and authorization sidecars for east-west communication. This reflects production patterns used by companies at scale (Google, Netflix, Uber) and provides the best balance of security and operational efficiency.

## Decision Drivers

* Need for fine-grained access control across all microservices (north-south and east-west)
* Requirement to validate every request without trusting network location
* Centralized policy management and consistent enforcement
* Performance optimization with minimal latency overhead
* Zero code changes required in services for authorization logic
* Enhanced auditability and compliance capabilities
* Support for modern OIDC/OAuth2 token-based authentication
* Scalability of security policies independent of service deployment
* Clear separation between authentication and authorization responsibilities

## Considered Options

* Perimeter-based security with VPN access
* Service-level authentication and authorization with direct integration
* Zero trust with API gateway and authorization sidecars
* Zero trust with IAM introspection and policy engine hooks

## Decision Outcome

Chosen option: "Zero trust with API gateway and authorization sidecars", because it provides the best balance of security, performance, and operational simplicity. API gateways handle token validation for north-south traffic, while authorization sidecars (OPA/Envoy) handle token validation and policy enforcement for east-west traffic, eliminating service code complexity while maintaining security guarantees.

**Implementation Pattern**: Sidecar deployment with OPA/Envoy proxies handling all authorization decisions, following proven patterns used by Netflix, Google, and Uber at scale.

### Authorization Architecture

**Core principle**: Every request MUST be validated and authorized, but services don't implement authorization logic themselves.

#### Sidecar-Based Authorization Flow

**Deployment Architecture:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Service   │───▶│ Auth Sidecar │───▶│ Target Svc  │
│             │    │ (OPA/Envoy)  │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                   ┌──────────────┐
                   │ Policy Engine│
                   │ (Remote API) │
                   └──────────────┘
```

**For East-West Traffic (Service-to-Service):**
- All service communication flows through authorization sidecars
- Sidecars validate JWT tokens locally (cryptographic verification)
- Sidecars query policy engines (OPA/OpenFGA) for authorization decisions
- Services receive only authorized requests - no auth code needed

**For North-South Traffic (Through Gateway):**
- API gateway validates tokens and performs coarse-grained authorization
- Authorization sidecars provide defense-in-depth with fine-grained policies
- Consistent authorization model for both external and internal traffic

### Consequences

* Good, because services have zero authorization code - focus purely on business logic
* Good, because consistent authorization across all services with zero configuration drift
* Good, because authorization policies updated without service redeployment
* Good, because sidecar pattern is proven at scale (Google, Netflix, Uber production)
* Good, because API gateway provides first line of defense for external access
* Good, because fine-grained ReBAC/ABAC policies supported through specialized engines
* Good, because centralized audit trails and monitoring through sidecars
* Good, because industry-standard approach with mature tooling ecosystem
* Bad, because additional infrastructure complexity with sidecar deployment
* Bad, because slight latency overhead (1-3ms) compared to direct service calls
* Bad, because requires container orchestration platform (Kubernetes, etc.)

### Confirmation

Implementation compliance will be confirmed through:
* Architecture reviews ensuring proper API gateway token validation
* Security audits verifying 100% of services have authorization sidecars
* Network policies confirming all service traffic flows through sidecars
* Policy testing to validate authorization rules work correctly for both traffic types
* Performance testing ensuring <5ms authorization overhead
* Monitoring dashboards showing sidecar health and policy engine metrics

## Pros and Cons of the Options

### Perimeter-based security with VPN access

Traditional approach using network-level security with VPN access for internal services.

```sh
[External Client] → [VPN Gateway] → [Internal Network (Trusted Zone)]
                                           ↓
                              [Service A] ↔ [Service B] ↔ [Service C]
```

* Good, because simple to understand and implement initially
* Good, because minimal changes required to existing services
* Neutral, because works well for simple, monolithic applications
* Bad, because assumes internal network is trusted (breach = full access)
* Bad, because difficult to implement fine-grained access controls
* Bad, because poor auditability and limited visibility into service access
* Bad, because no control over east-west traffic patterns

### Service-level authentication and authorization with direct integration

Services implement JWT validation and policy engine integration directly in application code.

* Good, because minimal infrastructure - no sidecars required
* Good, because direct control over authorization logic in service code
* Bad, because every service team must implement authentication/authorization correctly
* Bad, because authorization code scattered across all services (inconsistency risk)
* Bad, because difficult to ensure uniform security across all teams

### Zero trust with IAM introspection and policy engine hooks

API gateway and services call IAM introspection endpoint which integrates with policy engines for combined authentication and authorization decisions.

```sh
# North-South Traffic
[External Client] → [API Gateway] → [IAM Introspection + OPA] → [Service A]

# East-West Traffic  
[Service A] → [IAM Introspection + OPA] → [Service B]
```

* Good, because single call provides both authentication and authorization decisions
* Good, because leverages RFC 7662 standard introspection with policy engine extensions
* Good, because consistent approach for both north-south and east-west traffic
* Good, because centralized policy decisions through IAM+OPA integration
* Good, because enhanced introspection response can include permissions and context
* Good, because works well with legacy systems that support OAuth introspection
* Neutral, because requires IAM system that supports policy engine hooks
* Bad, because all requests must call IAM endpoint (potential performance bottleneck)
* Bad, because single point of failure if IAM system is unavailable
* Bad, because limited to IAM systems with extensibility capabilities

### Zero trust with API gateway and authorization sidecars

Authorization handled by sidecars (OPA/Envoy) with services focusing purely on business logic.

* Good, because zero authorization code in services - eliminates implementation errors
* Good, because consistent authorization enforcement across all services
* Good, because proven pattern at scale - used by Netflix, Google, Uber, Airbnb
* Good, because mature tooling ecosystem (Envoy, OPA, Istio)
* Bad, because additional operational complexity with sidecar management
* Bad, because slight performance overhead (1-3ms per request)

## More Information

**Architecture Components:**
- **API Gateway (North-South)**: Envoy, NGINX, Kong, Istio Gateway, Traefik
- **Authorization Sidecars**: Envoy + OPA, Envoy + OpenFGA, NGINX + OPA
- **Policy Engines**: OPA (Open Policy Agent), OpenFGA, Cedar
- **Identity Provider**: OIDC/OAuth2 compliant systems (Keycloak, Auth0, Okta)
- **Token Validation Libraries**: JWT libraries for signature and claims validation (jose, jsonwebtoken, etc.)
- **IAM with Policy Hooks**: Keycloak (authorization services), Auth0 (rules/actions), Okta (hooks)

**Implementation Patterns:**
- **Sidecar Authorization**: Authorization sidecars handle token validation and policy enforcement
- **IAM Introspection**: Services call IAM introspection endpoint (RFC 7662) which queries policy engines and returns enhanced responses
- **Direct Integration**: Services validate tokens offline (using public keys) and call policy engines directly for authorization decisions
- **Recommended Approach**: Sidecar-based authorization for operational simplicity and consistency

**Sidecar Implementation Options:**
- **Envoy + OPA**: Industry standard, used by Istio service mesh
- **Envoy + OpenFGA**: For relationship-based authorization
- **NGINX + OPA**: Lightweight alternative
- **Kong + OPA**: API gateway with sidecar capabilities

**Production Examples:**
- **Netflix**: Zuul/Envoy sidecars + custom authorization
- **Google**: Envoy sidecars + Zanzibar authorization
- **Uber**: Envoy sidecars + OPA for policy decisions
- **Airbnb**: Envoy sidecars + custom auth services

**Performance Characteristics:**
- **Token validation**: <1ms (local cryptographic verification)
- **Sidecar overhead**: 1-3ms additional latency
- **Policy decision**: 5-50ms depending on complexity and caching
- **Total overhead**: Typically 5-10ms for cached decisions

**Traffic Flow Definitions:**
- **North-South Traffic**: External users/clients accessing internal services through API Gateway (gateway validates, sidecars provide defense-in-depth)
- **East-West Traffic**: Service-to-service communication where sidecars validate tokens and check policies (mandatory - no gateway present)

**Implementation Timeline:**
- Phase 1: Deploy API gateway with OIDC token validation (north-south)
- Phase 2: Select and deploy policy engine infrastructure
- Phase 3: Deploy authorization sidecars to all services (for east-west traffic)
- Phase 4: Implement policy engine integration in sidecars for authorization decisions
- Phase 5: Define and deploy fine-grained policies, remove embedded auth logic
- Phase 6: Security audit to verify validation at all service boundaries

**Success Metrics:**
- API gateway validates all north-south traffic
- Authorization sidecars deployed to 100% of services (critical for east-west)
- Sidecar-based authorization for all service-to-service communication
- Sub-10ms authorization overhead for 95% of requests
- 99.9% API gateway and sidecar availability
- Centralized audit logs for all authorization decisions
- Zero services bypassing sidecar authorization
- Zero instances of implicit trust anti-patterns in code reviews

**Standards References:**
- **NIST SP 800-207**: "Zero Trust Architecture" - https://csrc.nist.gov/publications/detail/sp/800-207/final
- **CISA Zero Trust Maturity Model**: https://www.cisa.gov/zero-trust-maturity-model
- **Google BeyondCorp**: https://research.google/pubs/pub43231/
- **OPA Documentation**: https://www.openpolicyagent.org/docs/latest/
- **OpenFGA Documentation**: https://openfga.dev/docs/
- **Cedar Documentation**: https://docs.cedarpolicy.com/
- **RFC 7519**: JSON Web Token (JWT) - https://tools.ietf.org/html/rfc7519
- **RFC 7662**: OAuth 2.0 Token Introspection - https://tools.ietf.org/html/rfc7662
- **Envoy Authorization**: https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_authz_filter
- **Istio Authorization Policies**: https://istio.io/latest/docs/reference/config/security/authorization-policy/

This decision should be re-evaluated if sidecar operational complexity exceeds acceptable limits, if performance overhead becomes problematic, or if direct integration proves more suitable for specific organizational constraints.
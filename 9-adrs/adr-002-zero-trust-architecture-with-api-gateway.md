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

### Service-level authentication and authorization with direct integration

Services implement JWT validation and policy engine integration directly in application code.

* Good, because minimal infrastructure - no sidecars required
* Good, because direct control over authorization logic in service code
* Bad, because every service team must implement authentication/authorization correctly
* Bad, because authorization code scattered across all services (inconsistency risk)
* Bad, because difficult to ensure uniform security across all teams

### Zero trust with API gateway and authorization sidecars

Authorization handled by sidecars (OPA/Envoy) with services focusing purely on business logic.

* Good, because zero authorization code in services - eliminates implementation errors
* Good, because consistent authorization enforcement across all services
* Good, because proven pattern at scale - used by Netflix, Google, Uber, Airbnb
* Good, because mature tooling ecosystem (Envoy, OPA, Istio)
* Bad, because additional operational complexity with sidecar management
* Bad, because slight performance overhead (1-3ms per request)

## More Information

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

This decision should be re-evaluated if sidecar operational complexity exceeds acceptable limits, if performance overhead becomes problematic, or if direct integration proves more suitable for specific organizational constraints.
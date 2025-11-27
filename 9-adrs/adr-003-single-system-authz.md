---
# Configuration for the Jekyll template "Just the Docs"
parent: Decisions
nav_order: 105
title: Authorization Architecture - Single System Approach

status: "proposed"
date: 2025-11-27
decision-makers: "Architecture Team, Security Team"
consulted: "Platform Engineering Team, Identity Management Team"
informed: "Development Teams, Operations Team"
---
<!-- markdownlint-disable-next-line MD025 -->

# Authorization Architecture - Single System Approach

## Context and Problem Statement

Our Zero Trust Architecture requires fine-grained authorization decisions for microservices. We need to choose between policy-based authorization (OPA with RBAC/ABAC) and relationship-based authorization (OpenFGA with ReBAC) systems. While both models have strengths, operating multiple authorization systems introduces significant operational complexity that most organizations want to avoid.

**Production Reality**: Companies like Netflix, Google, and Uber typically choose one primary authorization model that handles 80-90% of their use cases, rather than managing hybrid systems.

Relates to:
- [ADR on Zero Trust Architecture with API Gateway and Sidecar Authorization](./adr-002-zero-trust-architecture-with-api-gateway.md)

## Decision Drivers

* Minimize operational complexity and infrastructure overhead
* Choose authorization model that fits majority (80%+) of use cases
* Ensure consistent authorization approach across all teams
* Optimize for developer experience and reduced cognitive load
* Enable efficient authorization decisions with minimal latency
* Support future growth without architectural complexity
* Align with proven patterns from production systems at scale

## Considered Options

* OPA-only architecture for policy-based authorization (RBAC/ABAC)
* OpenFGA-only architecture for relationship-based authorization (ReBAC)
* Hybrid architecture with both OPA and OpenFGA

## Decision Outcome

Chosen option: "OPA-only architecture for policy-based authorization", because it provides the best balance of functionality, operational simplicity, and developer familiarity. OPA can handle the majority of authorization scenarios through policies, with relationship data bundled when needed for specific use cases.

**Rationale**: Most enterprise authorization needs (90%+) are policy-based (roles, attributes, business rules) rather than complex relationship traversal. OPA's maturity, ecosystem, and operational simplicity make it the pragmatic choice for most organizations.

### Consequences

* Good, because single authorization system eliminates operational complexity
* Good, because OPA handles RBAC, ABAC, and business logic policies efficiently
* Good, because mature ecosystem with extensive tooling and community support
* Good, because familiar policy language (Rego) for security teams
* Good, because local evaluation provides consistent low latency
* Good, because simplified mental model for developers (one authorization approach)
* Good, because proven at scale by Netflix, Uber, and other production systems
* Bad, because complex relationship traversal requires workarounds or data bundling
* Bad, because real-time relationship changes may require policy bundle updates
* Bad, because bulk operations (list filtering) less efficient than specialized ReBAC systems

### Confirmation

Implementation compliance will be confirmed through:
* Security audits verifying OPA integration in 100% of services
* Performance testing showing <10ms authorization response time for 95% of requests
* Policy coverage analysis ensuring authorization patterns work for all use cases
* Developer feedback confirming ease of use and mental model clarity
* Operational reviews showing acceptable infrastructure complexity

## Pros and Cons of the Options

### OPA-only architecture for policy-based authorization (RBAC/ABAC)

Use Open Policy Agent for all authorization decisions with policies written in Rego.

```
Service ──▶ OPA Sidecar ──▶ Decision
              │
         Policy Bundle
       (Roles, Rules, Data)
```

* Good, because single authorization system with minimal operational overhead
* Good, because handles 90%+ of enterprise authorization scenarios effectively
* Good, because mature ecosystem with extensive tooling (testing, debugging, IDE support)
* Good, because local policy evaluation provides consistent sub-5ms latency
* Good, because security teams can manage centralized policies without service deployments
* Good, because proven at scale by Netflix, Uber, Airbnb production systems
* Good, because flexible policy language supports complex business logic
* Neutral, because requires modeling relationships as policy data when needed
* Bad, because less efficient for complex hierarchical relationship queries
* Bad, because bulk list operations require custom implementation

### OpenFGA-only architecture for relationship-based authorization (ReBAC)

Use OpenFGA for all authorization decisions by modeling permissions as relationships.

```
Service ──▶ OpenFGA API ──▶ Decision
              │
         Relationship Graph
       (Users, Groups, Resources)
```

* Good, because excellent for complex relationship-based authorization scenarios
* Good, because efficient bulk operations and list filtering capabilities  
* Good, because real-time relationship updates without policy deployment
* Good, because strong consistency guarantees for authorization decisions
* Good, because Google Zanzibar-inspired architecture proven at massive scale
* Neutral, because requires modeling all authorization as relationships
* Bad, because policy-like rules (time-based, business logic) complex to express
* Bad, because newer ecosystem with fewer tools compared to OPA
* Bad, because requires relationship modeling expertise across teams
* Bad, because network calls for every decision (higher latency than local OPA)

### Hybrid architecture with both OPA and OpenFGA

Maintain separate OPA and OpenFGA systems with routing logic.

* Good, because theoretically optimal authorization engine for each scenario
* Good, because handles both policy-based and relationship-based scenarios well
* Bad, because doubles operational complexity (two systems to manage)
* Bad, because requires complex routing logic prone to errors
* Bad, because mental overhead for teams deciding which system to use
* Bad, because inconsistent authorization patterns across the organization
* Bad, because very few production systems actually implement this successfully

## More Information

**OPA Implementation Architecture:**

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Service   │───▶│ OPA Sidecar  │───▶│  Decision   │
│             │    │              │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
                          │
                   ┌──────────────┐
                   │ Policy Bundle│
                   │ Management   │
                   └──────────────┘
```

**Handling Relationship Scenarios with OPA:**

**Approach 1 - Data Bundles:**
```rego
package authz

import future.keywords.if

# Team membership data bundled with policies
team_members := {
    "engineering": ["alice", "bob", "charlie"],
    "marketing": ["david", "eve"]
}

allow if {
    input.action == "view"
    input.resource.type == "document"
    input.user in team_members[input.resource.team]
}
```

**Approach 2 - External Data:**
```rego
package authz

import future.keywords.if

allow if {
    input.action == "view"
    team_membership_check
}

team_membership_check if {
    response := http.send({
        "method": "GET",
        "url": sprintf("http://user-service/teams/%s/members/%s", 
               [input.resource.team, input.user])
    })
    response.status_code == 200
}
```

**Production Examples:**
- **Netflix**: OPA with relationship data in policy bundles
- **Uber**: OPA with external service calls for dynamic relationships  
- **Airbnb**: OPA with cached relationship data updated periodically

**Performance Characteristics:**
- **Policy Evaluation**: <5ms for bundled data scenarios
- **External Calls**: 10-50ms when fetching relationship data
- **Bundle Size**: Typically <50MB for most organizations
- **Memory Usage**: 100-500MB per OPA instance with relationship data

**Migration Strategy:**
1. **Phase 1**: Deploy OPA sidecars with basic RBAC policies
2. **Phase 2**: Add attribute-based policies for business logic
3. **Phase 3**: Bundle critical relationship data with policies
4. **Phase 4**: Implement external service calls for dynamic relationships
5. **Phase 5**: Optimize bundle sizes and caching strategies

**When to Reconsider:**
- If >30% of authorization decisions require complex relationship traversal
- If real-time relationship updates become critical for business operations
- If bulk list operations become a significant performance bottleneck
- If the organization grows beyond OPA's relationship modeling capabilities

This decision should be re-evaluated if relationship complexity exceeds OPA's practical limits or if operational requirements change to favor specialized ReBAC systems.
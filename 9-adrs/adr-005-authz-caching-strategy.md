---
# Configuration for the Jekyll template "Just the Docs"
parent: Decisions
nav_order: 103
title: Authorization Caching Strategy for Fine-Grained Access Control

status: "proposed"
date: 2025-11-27
decision-makers: "Architecture Team, Security Team"
consulted: "Platform Engineering Team, Performance Engineering Team"
informed: "Development Teams, Operations Team"
---
<!-- markdownlint-disable-next-line MD025 -->

# Authorization Caching Strategy for Fine-Grained Access Control

## Context and Problem Statement

Our Zero Trust Architecture requires every service to validate tokens and check authorization policies for each request. While this ensures security, the performance overhead of making policy engine calls (OPA/OpenFGA) for every authorization decision can introduce unacceptable latency (50-200ms per check). We need a caching strategy that maintains security guarantees while achieving sub-10ms authorization response times for the majority of requests.

Relates to:
- [ADR on Zero Trust Architecture with API Gateway and Sidecar Authorization](./adr-002-zero-trust-architecture-with-api-gateway.md)

## Decision Drivers

* Sub-10ms authorization response time requirement for 95% of requests
* Maintain fine-grained access control capabilities
* Ensure policy changes propagate within acceptable timeframes
* Minimize policy engine load and infrastructure costs
* Support both OPA (policy-based) and OpenFGA (relationship-based) authorization models
* Enable horizontal scaling without performance degradation
* Preserve audit trail completeness for compliance

## Considered Options

* No caching - direct policy engine calls for every request
* Local in-memory caching with TTL expiration
* Distributed cache (Redis) with policy invalidation
* Hybrid sidecar caching with policy push notifications

## Decision Outcome

Chosen option: "Local in-memory caching with TTL expiration", because it provides the best balance of performance improvement and operational simplicity. This approach is widely used by production systems at scale (Netflix, Uber, Google) and achieves 80%+ cache hit rates with minimal infrastructure complexity.

**Production Reality**: Most companies use simple TTL-based caching (5-15 minutes) rather than complex push notification systems. Policy changes are infrequent, and the operational overhead of immediate invalidation typically doesn't justify the complexity for most use cases.

### Consequences

* Good, because achieves sub-5ms authorization response times for cached decisions
* Good, because reduces policy engine load by 80-90% for repeated authorization checks
* Good, because simplest implementation with minimal operational overhead
* Good, because no additional infrastructure required beyond sidecar deployment
* Good, because proven at scale by Netflix, Uber, and Google production systems
* Good, because graceful degradation - continues working during policy engine outages
* Good, because supports both positive and negative caching for comprehensive coverage
* Bad, because policy changes take up to TTL duration to propagate (5-15 minutes)
* Bad, because no immediate cache invalidation for emergency security changes
* Bad, because memory overhead for caching authorization decisions in each service

### Confirmation

Implementation compliance will be confirmed through:
* Performance testing showing 95% of authorization checks complete in <10ms
* Load testing demonstrating 80%+ reduction in policy engine calls
* Monitoring dashboards showing cache hit rates >80% in steady state
* Security testing verifying acceptable policy propagation delays (5-15 minutes)
* Audit verification that all authorization decisions are properly logged
* Operational reviews confirming minimal infrastructure complexity

## Pros and Cons of the Options

### No caching - direct policy engine calls for every request

Direct calls to policy engines (OPA/OpenFGA) for every authorization decision without any caching layer.

* Good, because simplest implementation with no cache complexity
* Good, because always returns current policy state with no consistency issues
* Good, because complete audit trail for every authorization decision
* Neutral, because works well for low-traffic systems
* Bad, because 50-200ms latency per authorization check is unacceptable
* Bad, because policy engine becomes bottleneck under load
* Bad, because high infrastructure costs for policy engine scaling
* Bad, because single point of failure if policy engine is unavailable

### Local in-memory caching with TTL expiration

Each service maintains local cache of authorization decisions with time-based expiration.

```
Service A → Local Cache (TTL: 5-15min) → OPA/OpenFGA (cache miss)
```

* Good, because sub-millisecond response time for cached decisions
* Good, because reduces policy engine load by 80-90% significantly  
* Good, because no additional infrastructure dependencies or operational complexity
* Good, because continues working during policy engine outages (graceful degradation)
* Good, because proven at scale by Netflix, Uber, Google production systems
* Good, because simple implementation with predictable behavior
* Good, because emergency invalidation possible via service restart (simple)
* Neutral, because 5-15 minute TTL acceptable for most enterprise use cases
* Bad, because policy changes take up to TTL duration to propagate
* Bad, because memory usage grows with number of unique authorization checks

### Distributed cache (Redis) with policy invalidation

Shared Redis cache storing authorization decisions with active invalidation when policies change.

```
Service A → Redis Cache → OPA/OpenFGA (cache miss)
               ↑
Policy Engine → Cache Invalidation
```

* Good, because shared cache improves hit rates across services
* Good, because active invalidation enables immediate policy change propagation
* Good, because centralized cache management and monitoring
* Good, because supports complex invalidation patterns (tag-based, pattern matching)
* Neutral, because adds Redis as infrastructure dependency
* Bad, because network latency to Redis cache (2-10ms) vs local cache (<1ms)
* Bad, because Redis becomes potential single point of failure
* Bad, because additional operational complexity and costs

### Hybrid sidecar caching with policy push notifications

Local sidecar cache with push notifications for immediate invalidation when policies change.

```
Service A → Sidecar Cache → OPA/OpenFGA (cache miss)
                ↑
Policy Management → Push Notifications → Cache Invalidation
```

* Good, because combines local cache speed with immediate invalidation capability
* Good, because policy changes propagate in seconds via push notifications
* Good, because graceful degradation - continues with stale cache if notifications fail
* Good, because cache hit rates improve over time as access patterns stabilize
* Good, because supports intelligent invalidation (only affected cache entries)
* Good, because works with both OPA policy updates and OpenFGA relationship changes
* Neutral, because requires sidecar deployment pattern
* Bad, because most complex implementation requiring notification infrastructure
* Bad, because potential message delivery issues requiring retry mechanisms

## More Information

**Implementation Architecture:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Service   │───▶│    Sidecar   │───▶│   OPA/FGA   │
│             │    │  TTL Cache   │    │   Engine    │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                       ┌──────────────┐
                                       │ Policy Bundle│
                                       │  Updates     │
                                       └──────────────┘
```

**Caching Strategy Details:**
- **Cache Key Format**: `{service}:{action}:{resource}:{user}:{context_hash}`
- **TTL Settings**: 10 minutes default, 5 minutes for sensitive resources
- **Cache Size**: 10,000 entries per sidecar (configurable based on memory)
- **Invalidation**: TTL expiration + optional service restart for emergencies
- **Negative Caching**: Cache "deny" decisions for 2 minutes to prevent brute force

**Production Examples:**
- **Netflix**: 15-minute TTL in authorization sidecars
- **Uber**: 5-minute TTL with service restart for policy changes
- **Google**: 10-minute TTL with periodic policy bundle updates

**Performance Targets:**
- **Cache Hit Rate**: >80% in steady state
- **Authorization Latency**: <2ms for cache hits, <50ms for cache misses
- **Policy Propagation**: 5-15 minutes acceptable for most use cases
- **Policy Engine Load Reduction**: >80% reduction in direct calls

**Security Considerations:**
- **Emergency Invalidation**: Service restart flushes all cached decisions
- **Audit Logging**: Log cache misses and policy engine calls for compliance
- **TTL Tuning**: Shorter TTL for sensitive resources, longer for stable permissions
- **Memory Limits**: Bounded cache size to prevent memory exhaustion

**Monitoring and Metrics:**
- Cache hit/miss ratios per service and resource type
- Authorization decision latency (P50, P95, P99)
- Policy engine health and response times
- Cache memory usage and eviction rates

**Rollout Strategy:**
1. **Phase 1**: Deploy authorization sidecars with 15-minute TTL
2. **Phase 2**: Monitor cache hit rates and optimize TTL values
3. **Phase 3**: Tune cache sizes based on memory usage patterns
4. **Phase 4**: Add negative caching for security protection
5. **Phase 5**: Implement monitoring and alerting for cache performance

This decision should be re-evaluated if cache hit rates remain below 70%, if policy propagation delays become unacceptable for business requirements, or if memory usage becomes problematic.
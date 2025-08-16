---
# Configuration for the Jekyll template "Just the Docs"
parent: Decisions
nav_order: 101
title: Event-Driven Processing with Polling Fallback
status: proposed
date: 2025-08-16
decision-makers: Rucio Core Team
consulted: Site Administrators, Storage System Experts
informed: Rucio User Community, Operations Teams
---

# Event-Driven Processing with Polling Fallback for Rucio Data Management

## Context and Problem Statement

Rucio currently relies on polling-based mechanisms to detect and process data management events (file transfers, replications, deletions). This approach creates significant latency in data processing pipelines and generates unnecessary load on storage systems through continuous polling. With growing data volumes and the need for near real-time data management, we need to evaluate transitioning to an event-driven architecture while maintaining system reliability and data consistency guarantees.

## Decision Drivers

* **Performance**: Reduce latency from minutes/hours to seconds for data management operations
* **Scalability**: Handle increasing data volumes without proportional infrastructure growth
* **Resource Efficiency**: Minimize unnecessary polling load on storage systems and databases
* **Reliability**: Maintain strong consistency guarantees and fault tolerance
* **Backward Compatibility**: Ensure smooth transition without breaking existing workflows
* **Operational Complexity**: Balance architectural benefits with maintainability

## Considered Options

* **Pure Event-Driven Architecture**: Complete transition to event-based processing with eventual consistency
* **Hybrid Event-Driven with Polling Fallback**: Primary event processing with polling safety net
* **Enhanced Polling with Optimization**: Improved current approach with smart polling intervals
* **Status Quo**: Continue with existing polling-based architecture

## Decision Outcome

Chosen option: "Hybrid Event-Driven with Polling Fallback", because it provides the performance benefits of event-driven processing while maintaining the reliability guarantees of the current system through a polling safety net.

### Consequences

* Good, because reduces average processing latency from minutes to seconds
* Good, because decreases load on storage systems and databases by 70-80%
* Good, because provides graceful degradation when event systems are unavailable
* Good, because allows gradual rollout and easy rollback if issues arise
* Bad, because increases architectural complexity with dual processing paths
* Bad, because requires maintaining both event and polling codebases initially
* Neutral, because eventual consistency model may require application-level handling

### Confirmation

Implementation compliance will be confirmed through:
- Performance benchmarks showing <30s average processing time vs current 5-15 minutes
- Load testing demonstrating reduced database query volume
- Chaos engineering tests validating fallback mechanisms
- Integration tests ensuring data consistency across both processing paths

## Pros and Cons of the Options

### Hybrid Event-Driven with Polling Fallback

Event-driven processing with automatic fallback to polling when events are missed or delayed.

* Good, because provides immediate performance improvements with safety guarantees
* Good, because allows incremental adoption across different storage systems
* Good, because maintains backward compatibility during transition period
* Good, because handles network partitions and event system failures gracefully
* Neutral, because requires duplicate logic for event and polling paths initially
* Bad, because increases operational complexity with multiple monitoring systems

### Pure Event-Driven Architecture

Complete replacement of polling with event-based processing using message queues and webhooks.

* Good, because maximizes performance and resource efficiency gains
* Good, because simplifies architecture long-term with single processing model
* Good, because aligns with modern distributed system patterns
* Bad, because creates single point of failure without polling safety net
* Bad, because eventual consistency may break existing strict consistency assumptions
* Bad, because difficult to rollback if critical issues emerge

### Enhanced Polling with Optimization

Improvements to current polling approach with adaptive intervals and caching.

* Good, because minimal risk and complexity increase
* Good, because maintains current consistency guarantees exactly
* Good, because easier to implement and test incrementally
* Neutral, because provides moderate performance improvements
* Bad, because still fundamentally limited by polling frequency vs load tradeoff
* Bad, because doesn't address core scalability concerns

### Status Quo

Continue with existing polling-based architecture without changes.

* Good, because zero implementation risk or operational changes
* Good, because maintains all current consistency and reliability properties
* Bad, because performance and scalability issues will worsen with data growth
* Bad, because higher infrastructure costs as system scales
* Bad, because doesn't address user complaints about processing delays

## More Information

The hybrid approach will be implemented in phases:
1. **Phase 1**: Deploy event listeners alongside existing polling for monitoring
2. **Phase 2**: Enable event processing for low-risk operations (metadata updates)
3. **Phase 3**: Extend to critical operations (transfers, replications) with polling fallback
~~4. **Phase 4**: Optimize and potentially phase out polling for stable event sources~~

Success metrics include 80% reduction in polling frequency, <60s average processing time, and zero data consistency violations. The decision should be re-evaluated after 6 months of production usage to assess the potential for transitioning to pure event-driven processing.
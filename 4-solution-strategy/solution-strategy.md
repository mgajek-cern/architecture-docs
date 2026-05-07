# Solution Strategy

*To be defined with stakeholders – example below.*

## Core Architectural Decisions

### Database-Driven Workflow Pipeline

**Decision:** Use database state as the primary coordination mechanism between daemons rather than direct messaging.

**Rationale:**
- **Reliability** - Database transactions ensure workflow state consistency even during daemon failures
- **Scalability** - Multiple daemon instances can process work queues without complex coordination
- **Observability** - All workflow state is queryable and auditable through standard database tools
- **Simplicity** - Eliminates complex message broker failure scenarios and ordering guarantees

**Pattern:** Each daemon polls database for work, updates state, and triggers next stage through database writes.

### Declarative Rule-Based Data Management

**Decision:** Users express intent through declarative rules ("3 copies on different continents") rather than imperative commands.

**How it works:**
1. User creates **Rule**: "Dataset X needs 3 replicas with constraint Y"
2. **Judge Evaluator** daemon translates rules into specific **Requests**: "Copy file A from Site 1 to Site 2"
3. **Transfer daemons** execute requests through external transfer tools
4. **System maintains** desired state automatically (healing, cleanup, etc.)

**Benefits:**
- **Intent-based** - Users specify what they want, not how to achieve it
- **Self-healing** - System continuously works toward declared state
- **Policy enforcement** - Rules encode institutional data management policies
- **Flexibility** - Same rule can adapt to changing infrastructure

### Hybrid Architecture Pattern

**State-Driven Workflow System with Service Boundaries**

- **Database state transitions** drive workflow progression
- **Polling-based daemons** detect and act on state changes
- **REST API** provides synchronous intent submission interface
- **Specialized daemons** handle distinct responsibilities (transfer, cleanup, monitoring)
- **Stateless worker model** enables horizontal scaling and fault tolerance

### Technology Strategy

**Persistence-Centric Design:**
- **SQLAlchemy ORM** abstracts database differences (MySQL, PostgreSQL, Oracle)
- **Alembic migrations** enable schema evolution across distributed deployments
- **External system integration** through standardized protocols (WebDAV, S3, XRootD)

**Operational Strategy:**
- **Container-first** deployment for consistency across sites
- **Protocol diversity** to integrate with heterogeneous storage infrastructure  
- **Federation-ready** design supporting multi-site catalog synchronization

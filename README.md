# architecture-docs

## Summary

This repository contains unofficial architecture documentation on the Rucio project.
Its primary goal is to provide a minimal and focused understanding of the system (building blocks, communication between components and systems, relevant cross-cutting concepts, etc.). It is intended as a lightweight reference to support personal comprehension and quick lookup, rather than as a comprehensive or authoritative source.

## References

- [What is Rucio?](https://rucio.github.io/documentation/started/what_is_rucio)
- [Rucio daemons](https://rucio.github.io/documentation/started/main_components/daemons)
- [Rucio Project Structure](https://rucio.github.io/documentation/developer/project_structure)
- [arc42 overview](https://arc42.org/overview)
- [Markdown Architectural Decision Records](https://adr.github.io/madr/)

## arc42 chapters

TODO(mgajek-cern): Eventually setup Jekyll based project or use other static site generator tool 

### 1. Introduction and Goals

See [What is Rucio?](https://rucio.github.io/documentation/started/what_is_rucio)

### 2. Constraints

[Overview of constraints influencing the architecture can be found here](./2-constraints/architecture-constraints.md)

### 3. Context & Scope

![Context View](./diagrams/Context%20View.png)

| Name | Type | Description |
| --- | --- | --- |
| Rucio | Internal System | Scientific data management framework providing declarative policy-based data organization, transfer, and lifecycle management across distributed heterogeneous storage infrastructure |
| Workflow Management Systems | External System | Job and task orchestration platforms including HPC clusters with batch scheduling systems, container orchestration, and scientific workflow engines that coordinate with Rucio for data availability, computational processing, and output registration |
| Authentication Systems | External System | Identity and access management services providing user authentication and authorization through various protocols and credential mechanisms |
| Storage Systems | External System | Heterogeneous storage backends including traditional filesystems, object storage, tape archives, cloud storage and external data repositories (such as Copernicus, DestinE, EUCAIM) accessed through standardized protocols |
| Monitoring Systems | External System | Analytics and observability platforms that collect, process, and visualize system performance metrics, usage statistics, and operational health data, including research infrastructure services providing popularity analytics and domain-specific metadata services |
| Logging Systems | External System | Centralized logging infrastructure that aggregates, stores, and provides search capabilities for system events, audit trails, and troubleshooting information |
| Database Systems | External System | Transactional relational database management systems that serve as the persistence layer for catalog metadata, system state, and configuration data, including FAIR Data Points providing standardized metadata and data discovery services |
| Transfer Systems | External System | Data movement services and protocols that handle the physical transfer of files between storage endpoints with reliability, scheduling, and error handling capabilities |
| Messaging Systems | External System | Messaging services that enable asynchronous communication between distributed components, supporting event-driven architectures, decoupling, reliable message delivery, and catalogue change notifications to external applications |
| Caching Systems | External System | High-speed data stores that temporarily hold frequently accessed data to reduce latency, decrease load on primary data sources, and improve overall system performance through intelligent data placement algorithms |

---

[Stakeholder details are provided here](./3-scope-and-context/stakeholders.md)

### 4. Solution strategy

TODO(mgajek-cern): Add links if existing

### 5. Building Block views

#### Lvl 1

![Building Block Lvl 1 View](./diagrams/Building%20Block%20Lvl%201%20View.png)

**Workflow Pattern:**

1. *User/Client* → *REST API*: "Create replication rule: 3 copies on different continents"
2. *REST API* → *Database*: Records the rule as a database entry
3. *Daemons* → *Database*: Query for pending rules/tasks
4. *Daemons* → *Storage/Transfer systems*: Execute the actual data operations
5. *Daemons* → *Database*: Update completion status

#### Lvl 2

![Building Block Lvl 2 View](./diagrams/Building%20Block%20Lvl%202%20View.png)

See also: [Rucio Project Structure](https://rucio.github.io/documentation/developer/project_structure)

#### Lvl 3

##### Daemons

TODO(mgajek-cern): Decomposition

[For more information on Rucio daemons refer to this link](https://rucio.github.io/documentation/started/main_components/daemons)

### 6. Runtime view

TODO(mgajek-cern): Add links if existing

### 7. Deployment view

As of now, the system differentiates between development and production environments. Expanding this to include a **dedicated QA/staging environment** would enable isolated validation of changes before release. This environment could mirror production closely to ensure realistic testing.

### 7. Deployment View

*To be defined with stakeholders – example below.*

#### Environments

* **Development** – for active feature work and integration (single-node `docker-compose` or Kubernetes). Early static code analysis and security scans are applied here.
* **QA** – focused on functional, integration, regression, and security testing (including vulnerability scanning and dependency checks), often with mock or partial production data. Ensures features meet requirements and security standards before moving forward.
* **Staging** – a near-identical replica of production for final acceptance, load, security, and release validation under production-like conditions. Often the last checkpoint before deployment, including penetration testing and compliance checks.
* **Production** – multi-node, multi-site deployments for live operations with continuous security monitoring and incident response.

#### Deployment strategies

**Deployment strategies** such as **Blue-Green** use staging as the inactive environment to validate functionality, integration, performance, security, and release readiness before switching traffic. **Canary Releases** leverage QA/staging to ensure builds pass all required validations—including security scans—before gradual rollout to production. **GitOps** manages all environments from version-controlled definitions, enabling controlled rolling updates with automated rollback on failure, including security policy enforcement.

#### Development environment – Single Node (docker-compose)

```mermaid
graph TD

%% Core Rucio System
Rucio[rucio-dev<br>8443->443] -->|connects to| RucioDB[PostgreSQL<br>5432]
Rucio -->|communicates with| XRootD1[dev-xrd1<br>1094]
Rucio -->|communicates with| XRootD2[dev-xrd2<br>1095]
Rucio -->|communicates with| XRootD3[dev-xrd3<br>1096]
Rucio -->|communicates with| XRootD4[dev-xrd4<br>1097]
Rucio -->|communicates with| XRootD5[dev-xrd5<br>1098/8098]
Rucio -->|WebDAV| WebDAV[dev-web1<br>8099]
Rucio -->|SSH Transfer| SSH[dev-ssh1<br>2222->22]
Rucio -->|FTS Control| FTS[dev-fts<br>8446/8449]
FTS --> FTSDB[MySQL<br>3306]

%% Messaging
Rucio --> ActiveMQ[ActiveMQ<br>61613]
ActiveMQ --> Daemons[Various Daemons]

%% Monitoring & Metrics
Rucio --> InfluxDB[InfluxDB<br>8086]
InfluxDB --> Grafana[Grafana<br>3000]
Rucio --> Graphite[Graphite<br>8080]
Graphite --> Grafana

%% Logging
Rucio --> Logstash[Logstash<br>5044]
Logstash --> Elasticsearch[Elasticsearch<br>9200/9300]
Elasticsearch --> Kibana[Kibana<br>5601]
```

For more details, see the [Using the Standard Environment](https://rucio.github.io/documentation/operator/setting_up_demo#using-the-standard-environment) guide.

#### Development, QA, Staging and Production environments - Multi-Node (Kubernetes)

TODO(mgajek-cern): add diagram, links, some content

#### Production environments - Multi-Site (Kubernetes Federation)

TODO(mgajek-cern): add diagram, links, some content

### 8. Crosscutting concepts

Refer to [Accounting and quota web page](https://rucio.github.io/documentation/started/concepts/accounting_and_quota) and subsequent sections.

### 9. Architectural decisions

TODO(mgajek-cern): Dedicated folder with .md content and add links if existing

### 10. Quality requirements

[Overview of quality requirements can be found here](./10-quality-requirements/quality-requirements.md)

### 11. Risks & technical debt

TODO(mgajek-cern): Add links if existing

### 12. Glossary

TODO(mgajek-cern): Add links if existing

#### Testing definitions for different environments

* **Functional/API testing** – verifies each feature or API behaves as expected.
* **Regression testing** – re-runs existing tests automatically on code changes to catch breaks early.
* **Integration testing** – verifies components/services interact correctly.
* **Acceptance testing** – final check that system meets business and security requirements before release.
* **Load testing** – measures performance under expected or heavy usage.
* **Security testing** – includes static analysis, vulnerability scans, penetration tests, and compliance validation across environments.
* **Release validation** – confirms the build is correct, stable, secure, and production-ready.



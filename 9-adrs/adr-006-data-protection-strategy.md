---
# Configuration for the Jekyll template "Just the Docs"
parent: Decisions
nav_order: 106
title: Data Protection Strategy - Encryption and Compliance

status: "proposed"
date: 2025-11-27
decision-makers: "Architecture Team, Security Team"
consulted: "Platform Engineering Team, Compliance Team, Legal Team"
informed: "Development Teams, Operations Team"
---
<!-- markdownlint-disable-next-line MD025 -->

# Data Protection Strategy - Encryption and Compliance

## Context and Problem Statement

Our distributed systems handle sensitive data that must be protected against unauthorized access, data breaches, and regulatory violations. We need a comprehensive data protection strategy that covers encryption at rest, encryption in transit, and compliance with regulations like GDPR, HIPAA, and SOX. The strategy must balance security requirements with operational efficiency and development velocity.

Relates to:
- [ADR on Zero Trust Architecture with API Gateway and Sidecar Authorization](./adr-zero-trust-architecture-updated.md)

## Decision Drivers

* Protect sensitive data from unauthorized access and breaches
* Meet regulatory compliance requirements (GDPR, HIPAA, SOX, PCI DSS)
* Ensure data integrity and confidentiality throughout data lifecycle
* Minimize performance impact while maintaining strong security posture
* Support modern cloud-native architectures and microservices
* Enable secure data sharing and processing across services
* Simplify key management and rotation procedures

## Considered Options

* Basic TLS/SSL with database encryption
* Comprehensive encryption strategy with centralized key management
* Application-level encryption with distributed key management

## Decision Outcome

Chosen option: "Comprehensive encryption strategy with centralized key management", because it provides enterprise-grade security, meets regulatory requirements, and offers operational simplicity through centralized key management while supporting modern distributed architectures.

### Consequences

* Good, because provides defense-in-depth with encryption at rest, in transit, and in use
* Good, because meets GDPR, HIPAA, SOX, and PCI DSS compliance requirements
* Good, because centralized key management simplifies operations and rotation
* Good, because supports modern cloud-native and microservices architectures
* Good, because industry-standard approach used by enterprises at scale
* Good, because enables secure data sharing between services and partners
* Bad, because increases complexity with key management infrastructure
* Bad, because slight performance overhead for encryption/decryption operations
* Bad, because requires careful planning for key rotation and recovery procedures

### Confirmation

Implementation compliance will be confirmed through:
* Security audits verifying encryption implementation across all data stores
* Compliance reviews confirming adherence to GDPR, HIPAA, and SOX requirements
* Performance testing ensuring encryption overhead <5ms for typical operations
* Key management testing validating rotation and recovery procedures
* Penetration testing confirming data protection against common attack vectors
* Monitoring dashboards showing encryption coverage and key health metrics

## Pros and Cons of the Options

### Basic TLS/SSL with database encryption

Use standard TLS for data in transit and database-level encryption for data at rest.

```
Client ──TLS──▶ Service ──TLS──▶ Database (encrypted storage)
```

* Good, because simple implementation with minimal operational overhead
* Good, because widely supported by cloud providers and databases
* Good, because adequate for basic compliance requirements
* Neutral, because works well for simple monolithic applications
* Bad, because limited granular control over encryption keys
* Bad, because insufficient for strict regulatory requirements (HIPAA, SOX)
* Bad, because data potentially visible to database administrators
* Bad, because limited protection for data in use during processing

### Comprehensive encryption strategy with centralized key management

Full encryption strategy covering all data states with enterprise key management system.

```
Client ──mTLS──▶ Service ──encrypted data──▶ HSM/KMS ──keys──▶ Storage
                    │                           │
              Application-level           Centralized Key
               Encryption              Management & Rotation
```

* Good, because comprehensive protection for data at rest, in transit, and in use
* Good, because meets strict regulatory requirements (GDPR, HIPAA, SOX, PCI DSS)
* Good, because centralized key management simplifies operations and compliance
* Good, because supports fine-grained access controls and data classification
* Good, because enables secure multi-party computation and confidential computing
* Good, because industry-standard approach for enterprise security
* Neutral, because requires investment in key management infrastructure
* Bad, because increased complexity in implementation and operations
* Bad, because performance overhead for encryption operations

### Application-level encryption with distributed key management

Each service manages its own encryption keys and handles data protection independently.

```
Service A ──local keys──▶ Encrypted Data ──▶ Storage
Service B ──local keys──▶ Encrypted Data ──▶ Storage
```

* Good, because maximum control over encryption implementation per service
* Good, because reduced dependency on centralized infrastructure
* Good, because potentially better performance with local key caching
* Neutral, because suitable for services with isolated data requirements
* Bad, because complex key sharing for cross-service data access
* Bad, because difficult to ensure consistent security policies across services
* Bad, because compliance auditing becomes extremely complex
* Bad, because high risk of implementation errors and security gaps

## More Information

**Encryption Implementation Strategy:**

**Data at Rest:**
- **Algorithm**: AES-256-GCM for symmetric encryption
- **Key Management**: AWS KMS, Azure Key Vault, or HashiCorp Vault
- **Database**: Transparent Data Encryption (TDE) + application-level encryption
- **Object Storage**: Server-side encryption with customer-managed keys
- **Backups**: Encrypted using separate key rotation schedule

**Data in Transit:**
- **External Traffic**: TLS 1.3 with perfect forward secrecy
- **Service-to-Service**: mTLS with short-lived certificates (24-hour rotation)
- **Database Connections**: TLS with certificate pinning
- **Message Queues**: End-to-end encryption for sensitive payloads
- **API Gateway**: TLS termination with re-encryption to backend services

**Data in Use (Confidential Computing):**
- **Sensitive Processing**: Intel SGX, AMD SEV, or AWS Nitro Enclaves
- **Key Processing**: Hardware Security Modules (HSMs) for cryptographic operations
- **Memory Protection**: Encrypted memory for sensitive data processing
- **Secure Enclaves**: Isolated execution environments for critical computations

**Key Management Architecture:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Service   │───▶│     KMS      │───▶│     HSM     │
│             │    │   (Vault)    │    │  (Hardware) │
└─────────────┘    └──────────────┘    └─────────────┘
                          │                    │
                   ┌──────────────┐    ┌──────────────┐
                   │ Key Rotation │    │ Audit Logs  │
                   │ & Lifecycle  │    │ & Compliance │
                   └──────────────┘    └──────────────┘
```

**Key Exchange Security Model:**

- No Raw Key Transmission: AES keys are never transmitted over networks in plaintext
- Envelope Encryption: Services request Data Encryption Keys (DEKs) from KMS, which are encrypted with master Key Encryption Keys (KEKs)
- Local Key Generation: KMS generates fresh DEKs per request, services receive both plaintext (temporary use) and encrypted versions (storage)
- Master Key Protection: KEKs remain in HSMs and never leave secure hardware boundaries
- Memory Safety: Plaintext keys are immediately cleared from service memory after use
- Zero Trust Key Access: All key operations require service authentication and authorization through mTLS

**Certificate Management Integration:**
- **Service Identity**: SPIFFE/SPIRE for automatic certificate enrollment
- **Certificate Lifecycle**: Cert-manager for Kubernetes-native certificate rotation
- **PKI Backend**: HashiCorp Vault PKI engine or internal CA
- **Auto-Renewal**: 24-hour certificate rotation with zero-downtime updates

**Regulatory Compliance Requirements:**

**GDPR (General Data Protection Regulation):**
- **Article 32**: "Appropriate technical and organizational measures" including encryption
- **Data Minimization**: Encrypt only necessary personal data fields
- **Right to Erasure**: Cryptographic deletion through key destruction
- **Data Portability**: Encrypted export/import capabilities

**HIPAA (Health Insurance Portability and Accountability Act):**
- **164.312(a)(2)(iv)**: Encryption of PHI in electronic form
- **164.312(e)(2)(ii)**: End-to-end encryption for PHI transmission
- **Business Associate Agreements**: Encryption requirements for third parties
- **Access Controls**: Integration with authorization systems for PHI access

**SOX (Sarbanes-Oxley Act):**
- **Section 404**: Internal controls over financial data protection
- **Audit Trail**: Encrypted logging of all financial data access
- **Segregation of Duties**: Role-based encryption key access
- **Change Management**: Controlled encryption policy updates

**PCI DSS (Payment Card Industry Data Security Standard):**
- **Requirement 3**: Protect stored cardholder data with strong encryption
- **Requirement 4**: Encrypt transmission of cardholder data across networks
- **Key Management**: PCI-compliant key management procedures
- **Regular Testing**: Quarterly encryption effectiveness validation

**Implementation Timeline:**
1. **Phase 1**: Deploy centralized key management infrastructure (KMS/Vault)
2. **Phase 2**: Implement TLS 1.3 and mTLS for all service communication
3. **Phase 3**: Enable database encryption and application-level encryption
4. **Phase 4**: Deploy confidential computing for sensitive data processing
5. **Phase 5**: Complete compliance audits and certification processes

**Performance and Monitoring:**
- **Encryption Overhead**: <5ms additional latency for typical operations
- **Key Operations**: <1ms for key retrieval from local cache
- **Throughput Impact**: <10% reduction for bulk data operations
- **Monitoring**: Real-time dashboards for encryption health and key rotation status

**Disaster Recovery:**
- **Key Escrow**: Secure backup of encryption keys in geographically distributed HSMs
- **Recovery Procedures**: Documented processes for key recovery and data restoration
- **Testing**: Quarterly disaster recovery drills including encryption key recovery
- **Business Continuity**: Failover procedures maintaining encryption requirements

**Standards and Best Practices:**
- **NIST Cybersecurity Framework**: Encryption as protective control
- **ISO 27001**: Information security management including encryption standards
- **FIPS 140-2**: Hardware security module certification requirements
- **Common Criteria**: Security evaluation for cryptographic modules

This decision should be re-evaluated if regulatory requirements change significantly, if performance impact becomes unacceptable, or if new encryption technologies provide substantial benefits over current approach.
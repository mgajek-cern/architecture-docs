# Storage Service Endpoints & Transfer Tools Guide

*For Rucio daemon concepts, see: [rucio-daemons-using-transfer-tools](./rucio-daemons-using-transfer-tools.md)*

## 📊 Storage Service Endpoints & Usage Summary

| **Protocol**            | **Endpoint Type / URL**                 | **Operations**                    | **How to Invoke (Tools/Methods)**                               | **Key Features / Status**                         |
| ----------------------- | --------------------------------------- | --------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| **WebDAV / HTTP-TPC**   | `https://storage.example.com/webdav/`   | List, upload, download, delete    | HTTP/WebDAV (`PROPFIND`, `GET`, `PUT`), tools: `curl`, `davfs2` | ✅ Primary standard; enables HTTP-TPC              |
| **XRootD**              | `root://xrootd.example.com//path/file`  | Streaming, read/write large files | `xrdcp`, XRootD client libraries                                | ✅ High-performance, widely used in HEP            |
| **HTTP/HTTPS**          | `https://storage.example.com/files/...` | Simple download/upload            | `curl`, `wget`, browser                                         | ✅ Universal fallback; also used in TPC            |
| **S3 (Object Storage)** | `s3://bucket/path`                      | Upload, download, list objects    | AWS CLI, `s3cmd`, boto3                                         |  ⚠️ Typically accessed via gateways or signed URLs |
| **GridFTP**             | `gsiftp://storage.example.com/path`     | High-speed transfer, list         | `globus-url-copy`, `gfal-copy`                                  |  ⚠️ Deprecated / being phased out                  |
| **SRM**                 | `srm://storage.example.com/path`        | Tape staging, space reservation   | `srmcp`, `lcg-cp`                                               |  ⚠️ Deprecated; replaced by HTTP-based staging     |
| **Globus Endpoints**    | UUID-based managed endpoints            | Managed transfers                 | Globus CLI / Web UI                                             | ✅ Managed service, identity-driven transfers      |

## 🔐 Authentication & Authorization

| **Mechanism**          | **Usage**                     | **Notes**                                   |
| ---------------------- | ----------------------------- | ------------------------------------------- |
| **X.509 Certificates** | Legacy grid authentication    | Being phased out in favor of tokens         |
| **OAuth2 / OIDC**      | Modern authentication         | Used with token-based workflows             |
| **SciTokens / JWT**    | Authorization for data access | Common with HTTP-TPC and cloud integrations |

> ⚠️ Modern deployments should prioritize **token-based auth (OIDC/SciTokens)** over X.509.

## 🔧 Storage Systems & Technologies

| **Storage System**                  | **Type**               | **Protocols Supported**                | **Primary Use Case**                 | **Third-Party Copy Support** |
| ----------------------------------- | ---------------------- | -------------------------------------- | ------------------------------------ | ---------------------------- |
| **EOS**                             | Distributed storage    | XRootD, HTTP/WebDAV                    | Low-latency physics data access      | ✅ HTTP-TPC, XRootD-TPC       |
| **dCache**                          | Storage middleware     | WebDAV, XRootD, HTTP, (GridFTP legacy) | Disk + tape, multi-protocol          | ✅ Strong multi-protocol TPC  |
| **StoRM**                           | SRM-based system       | SRM, WebDAV, HTTP                      | Legacy grid storage                  | ⚠️ Limited modern relevance  |
| **HTTP-TPC gateways (e.g. Teapot)** | Transfer service layer | HTTP/HTTPS                             | Efficient third-party HTTP transfers | ✅ Native HTTP-TPC            |

## 🔄 Transfer Tool Operations

| **Operation**             | **Description**                    | **FTS Implementation**         | **Globus Implementation** | **Rucio Integration**             |
| ------------------------- | ---------------------------------- | ------------------------------ | ------------------------- | --------------------------------- |
| **Submit Transfer**       | Request transfer between endpoints | REST API submission            | CLI/Web UI                | Conveyor submitter daemon submits jobs      |
| **Poll Status**           | Check transfer progress            | REST API polling               | `globus task show`        | Conveyor poller daemon monitors            |
| **Receive Notifications** | Listen for transfer events         | Message queue (e.g., ActiveMQ) | Event streams             | Conveyor finisher daemon processes results |
| **Cancel Transfer**       | Abort transfers                    | REST API cancel                | `globus task cancel`      | User or system-triggered          |
| **Stage Files**           | Prepare tape-resident files        | HTTP/SRM-based staging         | N/A                       | Conveyor stager daemon                     |

## 🚀 Third-Party Copy (TPC) Mechanisms

| **TPC Type**    | **Protocol** | **Description**                           | **Benefits**                 | **Status**  |
| --------------- | ------------ | ----------------------------------------- | ---------------------------- | ----------- |
| **HTTP-TPC**    | HTTP/WebDAV  | Direct transfers via HTTP between storage | Standard, firewall-friendly  | ✅ Preferred |
| **XRootD-TPC**  | XRootD       | Native XRootD third-party transfers       | Low latency, high throughput | ✅ Preferred |
| **GridFTP-TPC** | GridFTP      | Direct GridFTP transfers                  | Parallel streams             | ⚠️ Legacy   |

*For HTTP-TPC technical details, see:* CERN *HTTP-TPC documentation*

## 🔗 How Components Work Together

```
(Control Plane)
User Request → Rucio → Transfer Tool (FTS / Globus)
                      ↓
(Data Plane)     Storage Endpoint ↔ Storage Endpoint
```

### **Important Distinction**

* **Rucio + FTS/Globus = control plane (orchestration only)**
* **Actual data flows directly between storage endpoints (TPC)**

## **Key Integration Points**

1. **Rucio** orchestrates policies, replication, and workflows
2. **File Transfer Service** handles high-throughput, policy-driven transfers
3. **Globus** provides managed, user-facing transfer services
4. Storage systems (e.g., **EOS**, **dCache**) expose protocol endpoints
5. **Third-party copy (TPC)** eliminates intermediate data hops
6. Protocols (HTTP, XRootD) implement the actual data movement

## **Best Practices**

* Prefer **HTTP-TPC and XRootD-TPC** for scalable data transfers
* Treat **GridFTP and SRM as legacy compatibility layers**
* Use **token-based authentication (OIDC, SciTokens)** instead of X.509 where possible
* Ensure storage endpoints support **native third-party copy (TPC)**
* Use **WebDAV/HTTP** for maximum interoperability
* Integrate S3 via **gateway endpoints or signed URLs**, not raw object storage in FTS workflows
* Use **Globus** primarily for user-driven or cross-institution transfers

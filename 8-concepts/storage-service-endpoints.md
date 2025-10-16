# Storage Service Endpoints & Transfer Tools Guide

*For Rucio daemon concepts, see: [rucio-daemons-using-transfer-tools](./rucio-daemons-using-transfer-tools.md)*

---

## 📊 Storage Service Endpoints & Usage Summary

| **Protocol** | **Endpoint Type / URL** | **Operations** | **How to Invoke (Tools/Methods)** | **Used by** | **Key Features** |
| ------------ | --------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------- | ----------------------- | ------------------------------------------ |
| **WebDAV** | `https://storage.example.com/webdav/` | List, upload, download, delete | HTTP/WebDAV methods (`PROPFIND`, `GET`, `PUT`), tools: `curl`, `davfs2` | FTS, Rucio | Standard HTTP-based, wide compatibility |
| **GridFTP** | `gsiftp://storage.example.com/path` | High-speed file transfer, list | `globus-url-copy`, `gfal-copy` CLI | FTS, Rucio | Optimized for large files, parallel streams |
| **XRootD** | `root://xrootd.example.com//path/file` | Streaming, read/write large files | `xrdcp` CLI, XRootD client libraries | FTS, Rucio | Low-latency, optimized for HEP data |
| **S3** | `s3://bucketname/path/to/object` | Upload, download, list objects | AWS CLI, `s3cmd`, boto3 (Python SDK) | Globus, cloud services | Object storage, cloud-native |
| **HTTP/HTTPS** | `https://storage.example.com/files/...` | Simple download/upload | `curl`, `wget`, browser | Fallback in FTS, Globus | Universal support, simple operations |
| **Globus** | Globus-managed endpoints (UUID-based) | Secure, managed transfer | Globus CLI/web UI (`globus transfer`) | Globus only | Managed authentication, monitoring |
| **SRM** | `srm://storage.example.com/path` | Tape staging, space reservation | `srmcp`, `lcg-cp` | FTS, legacy systems | Tape/disk management, space guarantees |

---

## 🔧 Storage Systems & Technologies

| **Storage System** | **Type** | **Protocols Supported** | **Primary Use Case** | **Third-Party Copy Support** |
| ------------------ | ------------------------- | ----------------------------------------- | ------------------------------------ | ----------------------------- |
| **EOS** | Distributed storage | XRootD, HTTP/WebDAV | Low-latency physics data access | ✅ Yes (HTTP-TPC, XRootD-TPC) |
| **dCache** | Storage middleware | GridFTP, WebDAV, XRootD, SRM | Multi-tier storage (disk/tape) | ✅ Yes (Multiple protocols) |
| **Storm** | SRM implementation | SRM, GridFTP, HTTP/WebDAV | Grid storage management | ✅ Yes (GridFTP-TPC) |
| **Teapot** | HTTP-TPC implementation | HTTP/HTTPS | Efficient HTTP transfers | ✅ Yes (Native HTTP-TPC) |

---

## 🔄 Transfer Tool Operations

| **Operation** | **Description** | **FTS Implementation** | **Globus Implementation** | **Rucio Integration** |
| ------------------------- | ------------------------------------------- | --------------------------------- | ---------------------------------- | ---------------------------------------- |
| **Submit Transfer** | Request transfer between endpoints | HTTP REST API submission | CLI/Web UI submission | Submits to FTS/Globus via conveyor |
| **Poll Status** | Check transfer progress | REST API status calls | `globus task show` | Monitors via poller daemon |
| **Receive Notifications** | Listen for transfer events | ActiveMQ message queue | Globus event streams | Finisher daemon processes notifications |
| **Cancel Transfer** | Abort active transfers | FTS REST API cancel | `globus task cancel` | Submitter can cancel jobs |
| **Stage Files** | Prepare tape files for transfer | SRM staging commands | N/A (disk only) | Stager daemon handles staging |
| **Verify Integrity** | Check file checksums | Built-in checksum verification | Built-in integrity checking | Reaper daemon validates transfers |

---

## 🚀 Third-Party Copy (TPC) Mechanisms

| **TPC Type** | **Protocol** | **Description** | **Benefits** | **Example** |
| ------------ | ------------ | -------------------------------------------- | ----------------------------------------- | ------------------------------------------------ |
| **HTTP-TPC** | HTTP/WebDAV | Direct HTTP transfers between storage | No intermediate client, standard protocol | Source pulls from destination via HTTP redirect |
| **GridFTP-TPC** | GridFTP | Direct GridFTP between endpoints | High performance, parallel streams | FTS orchestrates direct GridFTP transfer |
| **XRootD-TPC** | XRootD | Native XRootD third-party transfers | Low latency, optimized for HEP | Direct root:// to root:// copying |

*For HTTP-TPC technical details, see: [CERN HTTP-TPC Documentation](https://twiki.cern.ch/twiki/bin/view/LCG/HttpTpcTechnical)*

---

## 🔗 How Components Work Together

```
User Request → Rucio → Transfer Tool (FTS/Globus) → Storage Endpoints
                ↓                                          ↓
            Daemons manage:                        Protocols handle:
            - Submission                          - Authentication
            - Monitoring                          - Data transfer
            - Retry logic                         - Third-party copy
            - Cleanup                             - Integrity checks
```

### **Key Integration Points:**

1. **Rucio** orchestrates high-level data management policies
2. **FTS/Globus** handle actual transfer execution and monitoring
3. **Storage systems** (EOS, dCache, Storm) expose protocol endpoints
4. **Third-party copy** optimizes transfers by eliminating intermediaries
5. **Protocols** (WebDAV, GridFTP, XRootD, etc.) provide the actual transfer mechanisms

### **Best Practices:**
- Use GridFTP or XRootD for large scientific datasets
- Enable third-party copy for efficiency
- Implement WebDAV for broad compatibility
- Use SRM for tape storage management
- Deploy HTTP/HTTPS as universal fallback
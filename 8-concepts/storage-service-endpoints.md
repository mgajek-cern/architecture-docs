### Storage Service Endpoints & Usage Summary

| **Protocol**   | **Endpoint Type / URL**                 | **Operations**                    | **How to Invoke (Tools/Methods)**                                           | **Used by**             |
| -------------- | --------------------------------------- | --------------------------------- | --------------------------------------------------------------------------- | ----------------------- |
| **WebDAV**     | `https://storage.example.com/webdav/`   | List, upload, download, delete    | HTTP/WebDAV methods (`PROPFIND`, `GET`, `PUT`), tools like `curl`, `davfs2` | FTS, Rucio              |
| **GridFTP**    | `gsiftp://storage.example.com/path`     | High-speed file transfer, list    | `globus-url-copy`, `gfal-copy` CLI                                          | FTS, Rucio              |
| **XRootD**     | `root://xrootd.example.com//path/file`  | Streaming, read/write large files | `xrdcp` CLI, XRootD client libraries                                        | FTS, Rucio              |
| **S3**         | `s3://bucketname/path/to/object`        | Upload, download, list objects    | AWS CLI, `s3cmd`, boto3 (Python SDK)                                        | Globus, others          |
| **HTTP/HTTPS** | `https://storage.example.com/files/...` | Simple download/upload            | `curl`, `wget`, browser                                                     | Fallback in FTS, Globus |
| **Globus**     | Globus-managed endpoints (UUID-based)   | Secure, managed transfer          | Globus CLI/web UI (`globus transfer`)                                       | Globus only             |
| **SRM**        | `srm://storage.example.com/path`        | Tape staging, space reservation   | `srmcp`, `lcg-cp`                                                           | FTS, legacy systems     |

---

### Typical Operations for Transfer Tools (FTS, Globus, etc.)

| **Operation**             | **Description**                             | **Example Invocation**                           |
| ------------------------- | ------------------------------------------- | ------------------------------------------------ |
| **Submit Transfer**       | Request transfer of files between endpoints | FTS: submit via HTTP API or Globus CLI           |
| **Poll Status**           | Check progress of ongoing transfers         | FTS REST API calls or Globus transfer status     |
| **Receive Notifications** | Listen for transfer events (done/fail)      | Message queues (ActiveMQ) for FTS, Globus events |
| **Cancel Transfer**       | Abort active transfers                      | FTS API call, Globus CLI cancel                  |
| **Stage Files**           | Prepare files on tape/disk for transfer     | SRM commands, staging daemons                    |

---

### How FTS/Globus Use These Endpoints

* **FTS:** Submits transfer jobs to endpoints exposing GridFTP, WebDAV, SRM, XRootD, HTTP(S). It manages retries, integrity checks, and complex workflows via its API.
* **Globus:** Uses its own endpoints (UUID-based), which can wrap S3, HTTP, or other protocols, providing secure and reliable transfers with managed authentication and monitoring.
* Both interact with **storage service endpoints** by addressing protocol-specific URLs and invoking the right operations through clients or APIs.
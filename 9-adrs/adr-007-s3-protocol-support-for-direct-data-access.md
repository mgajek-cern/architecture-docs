---
parent: Decisions
nav_order: 105
title: S3 Protocol Support for External Data Access

status: "proposed"
date: 2025-02-10
decision-makers: "Architecture Team, Rucio Development Team"
consulted: "Operations Team, Security Team"
informed: "User Community, Storage Providers"
---

# S3 Protocol Support for External Data Access

## Context and Problem Statement

Rucio needs to support direct access to data stored in external S3-compatible object stores (e.g., Copernicus Data Space, commercial cloud providers) without copying data into Rucio-managed storage. Currently, Rucio lacks native S3 protocol support - existing protocols (GFAL2, WebDAV, XRootD) cannot interact with S3 APIs, preventing:

1. Direct client downloads via `rucio download` from S3 RSEs
2. Proper PFN generation with AWS Signature V4 signed URLs
3. Native boto3-based file operations (stat, exists, delete)

Users must either:
- Manually download via boto3 scripts outside Rucio
- Copy data to Rucio-managed storage (duplicating TB-scale datasets)
- Use workarounds with incomplete S3 support

## Decision Drivers

* Enable direct read access to external S3 data sources
* Support AWS Signature V4 URL signing for authenticated access
* Maintain compatibility with existing Rucio client workflows
* Minimize operational overhead (no data duplication)
* Support both read-only catalogs and read/write RSEs
* Preserve security via proper credential management
* Enable future FTS3 S3 replication capabilities

## Considered Options

1. **Add native S3 protocol (`s3boto.py`)** - Implement boto3-based protocol driver
2. **Extend GFAL2 with S3 support** - Wait for GFAL2 upstream S3 implementation
3. **External catalog only** - Use Rucio as metadata catalog, require manual downloads

## Decision Outcome

Chosen option: **"Add native S3 protocol (`s3boto.py`)"**, because it:
- Provides immediate S3 support without waiting for upstream changes
- Enables standard Rucio workflows (`rucio download`)
- Uses mature boto3 library with full S3 feature support
- Supports both read-only external catalogs and read/write RSEs
- Follows established Rucio protocol architecture patterns

### Implementation

**New Protocol File:** `rucio/rse/protocols/s3boto.py`
```python
class Default(protocol.RSEProtocol):
    """S3 protocol implementation using boto3"""
    
    def __init__(self, protocol_attr, rse_settings, logger=logging.log):
        super().__init__(protocol_attr, rse_settings, logger)
        self._s3_client = self._create_s3_client()
    
    def _create_s3_client(self):
        # Extract credentials from RSE attributes
        access_key = self.rse.get('s3_access_key')
        secret_key = self.rse.get('s3_secret_key')
        endpoint_url = self._build_endpoint_url()
        
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4')
        )
    
    def get(self, pfn, dest, transfer_timeout=None):
        bucket, key = self._parse_pfn(pfn)
        self._s3_client.download_file(bucket, key, dest)
    
    def put(self, source, target, source_dir=None, transfer_timeout=None):
        bucket, key = self._parse_pfn(target)
        self._s3_client.upload_file(source, bucket, key)
    
    def exists(self, pfn):
        bucket, key = self._parse_pfn(pfn)
        try:
            self._s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
```

**RSE Configuration Example:**
```bash
# Create non-deterministic RSE for external S3
rucio-admin rse add --non-deterministic COPERNICUS_S3

# Add S3 protocol
rucio-admin rse add-protocol COPERNICUS_S3 \
  --scheme https \
  --hostname eodata.dataspace.copernicus.eu \
  --port 443 \
  --prefix /eodata \
  --impl rucio.rse.protocols.s3boto.Default

# Set S3-specific attributes
rucio-admin rse set-attribute COPERNICUS_S3 --key s3_access_key --value AKIA...
rucio-admin rse set-attribute COPERNICUS_S3 --key s3_secret_key --value secret...
rucio-admin rse set-attribute COPERNICUS_S3 --key s3_url_style --value path
rucio-admin rse set-attribute COPERNICUS_S3 --key region --value eu-central-1
```

**DID/Replica Registration:**
```python
from rucio.client.replicaclient import ReplicaClient

rc = ReplicaClient()
files = [{
    'scope': 'eodata',
    'name': 'S2A_MSIL2A_20240115T235221_N0510_R130_T55HGS_20240116T021554.SAFE',
    'bytes': 1000000000,
    'adler32': 'deadbeef',
    'pfn': 'https://eodata.dataspace.copernicus.eu/eodata/Sentinel-2/MSI/L2A/2024/01/15/S2A_MSIL2A_...',
}]

rc.add_replicas(rse='COPERNICUS_S3', files=files)
```

**Client Usage:**
```bash
# Standard Rucio download now works with S3
rucio download eodata:S2A_MSIL2A_20240115T235221_N0510_R130_T55HGS_20240116T021554.SAFE
```

### Consequences

* Good, because enables immediate S3 support without upstream dependencies
* Good, because uses proven boto3 library (AWS-recommended)
* Good, because supports full S3 feature set (multipart, versioning, etc.)
* Good, because follows existing Rucio protocol architecture
* Good, because enables both read-only and read/write S3 RSEs
* Good, because supports AWS Signature V4 signed URLs natively
* Bad, because adds boto3/botocore dependency to Rucio
* Bad, because S3 credentials stored as RSE attributes (needs secure handling)
* Bad, because FTS3 replication uses separate S3 implementation (not this protocol)

### Confirmation

* Unit tests covering all S3 operations (get, put, delete, exists, stat)
* Integration tests with real S3-compatible endpoints
* Security audit of credential storage and handling
* Performance benchmarking vs native boto3 scripts
* Documentation for RSE operators and users
* Validation with production S3 providers (AWS, MinIO, Copernicus)

## Pros and Cons of the Options

### Add native S3 protocol (`s3boto.py`)

* Good, because provides immediate solution
* Good, because uses AWS-recommended boto3 library
* Good, because supports full S3 API features
* Good, because integrates with existing Rucio workflows
* Good, because enables both read-only and read/write scenarios
* Neutral, because adds dependency on boto3/botocore
* Bad, because requires secure credential management
* Bad, because separate from FTS3 S3 support

### Extend GFAL2 with S3 support

* Good, because would unify protocol ecosystem
* Good, because GFAL2 is existing Rucio dependency
* Bad, because GFAL2 upstream has no S3 support
* Bad, because would require upstream contribution and waiting
* Bad, because GFAL2 development velocity is slow
* Bad, because blocks immediate user needs

### External catalog only

* Good, because minimal Rucio changes
* Good, because treats S3 as pure metadata catalog
* Bad, because breaks standard Rucio workflows
* Bad, because requires custom download scripts
* Bad, because no integration with `rucio download`
* Bad, because poor user experience

## Implementation Plan

### Phase 1: Core Protocol (Week 1-2)
- [ ] Implement `s3boto.py` protocol class
- [ ] Add boto3 dependency to requirements
- [ ] Implement basic operations (get, put, exists, stat, delete)
- [ ] Add PFN parsing for path/host style URLs
- [ ] Implement S3 client creation with credentials

### Phase 2: Testing (Week 3)
- [ ] Unit tests for all operations
- [ ] Integration tests with MinIO local instance
- [ ] Integration tests with real S3/Copernicus
- [ ] Performance benchmarking
- [ ] Error handling validation

### Phase 3: Security & Documentation (Week 4)
- [ ] Security review of credential handling
- [ ] Operator documentation for RSE configuration
- [ ] User documentation for S3 RSE access
- [ ] Example configurations for common providers
- [ ] Migration guide from workarounds

### Phase 4: Production Rollout (Week 5-6)
- [ ] Deploy to test instance
- [ ] Validate with pilot users
- [ ] Deploy to production
- [ ] Monitor usage and performance
- [ ] Gather feedback and iterate

## More Information

**Credential Management:**
- S3 credentials stored as RSE attributes (encrypted at rest)
- Consider secret management integration (Vault, K8s secrets)
- Support IAM roles for AWS-hosted Rucio instances
- Document credential rotation procedures

**URL Signing:**
- Protocol generates pre-signed URLs for authenticated access
- Configurable signature lifetime (default: 3600s)
- Supports both path-style and virtual-host-style URLs
- Compatible with S3-compatible APIs (MinIO, Ceph, etc.)

**FTS3 Integration:**
- FTS3 has **separate** S3 support (does not use this protocol)
- This protocol is for **client operations** only
- Future: Investigate unified S3 credential management

**Supported Operations:**
| Operation | Supported | Notes |
|-----------|-----------|-------|
| Download (get) | ✅ | Native boto3 download |
| Upload (put) | ✅ | Native boto3 upload |
| Delete | ✅ | Single object deletion |
| Exists check | ✅ | HEAD operation |
| Stat | ✅ | Returns size, checksum (if ETag is MD5) |
| Rename | ❌ | S3 has no atomic rename |
| Multipart | ✅ | Handled by boto3 automatically |

**Alternative Implementations:**
- `ReadOnly` subclass for read-only external catalogs
- Custom retry logic for transient S3 errors
- Batch operations for bulk metadata queries
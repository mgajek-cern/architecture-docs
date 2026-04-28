---
parent: Decisions
nav_order: 108
title: Multi-IdP Token Issuance per RSE

status: "proposed"
date: 2026-04-28
decision-makers: "Architecture Team, Rucio Development Team"
consulted: "Operations Team, Security Team, FTS3 Team"
informed: "User Community, VO Representatives, Storage Providers"
---

# Multi-IdP Token Issuance per RSE

## Context and Problem Statement

Federated and cross-VO third-party copy (TPC) requires that source and destination storage endpoints can trust tokens from different OIDC issuers within a single transfer. Rucio currently couples token issuance to a single, deployment-wide IdP — `rucio.core.oidc.request_token()` cannot be told which IdP to ask. Real-world scenarios (e.g. data on a CILogon-trusting endpoint copied to a CERN-IAM-trusting endpoint) are blocked by this limitation, even though FTS3 already supports per-token issuers at the schema and executor level.

How can Rucio acquire source and destination tokens from distinct IdPs per RSE without invasive changes to FTS3 or the storage layer?

This ADR extends [ADR-004](./adr-004-token-propagation-strategy.md) — it does not supersede it. See also [concept](../8-concepts/multi-idp-third-party-copy.md).

**Invariant:** Each token used in a transfer MUST be minted against the issuer trusted by the corresponding RSE. Rucio is responsible for ensuring that issuer, audience, and scope are consistent with the RSE's policy at submission time.

**Scope boundary:** Token refresh during transfer remains FTS3's responsibility (handled by the fts_token daemon and unchanged by this decision). ADR-004 governs how Rucio propagates tokens to FTS3 — passthrough — and that propagation pattern is preserved.

## Decision Drivers

* Unblock federated and cross-VO TPC scenarios already requested by user communities
* Avoid schema migrations on the FTS3 side (already supports per-token issuers)
* Preserve backward compatibility for single-IdP deployments
* Keep operational surface manageable for site administrators
* Align with the WLCG JWT Profile and RFC 8693 token-exchange conformance

## Considered Options

1. **Per-RSE issuer attribute on the Rucio side** — add `RseAttr.OIDC_ISSUER`, dispatch `request_token()` per IdP
2. **Single-IdP federation broker** — deploy a federation gateway that brokers between Rucio and downstream IdPs
3. **Per-VO issuer mapping only** — map VO → issuer (coarser than per-RSE)
4. **Status quo** — require all participating endpoints to trust a single IdP

## Decision Outcome

Chosen option: **"Per-RSE issuer attribute on the Rucio side"**, because it:

- Aligns with how FTS3 already models tokens (`t_token.issuer`, `t_token_provider`)
- Requires no FTS3 schema migration
- Preserves backward compatibility through fallback to the existing single-IdP config
- Matches the granularity at which storage endpoints actually trust issuers (RSE-level, not VO-level)
- Avoids introducing a new federation broker as a single point of failure

### Implementation

**Identifier model.** This ADR distinguishes two identifiers and uses them consistently:

| Identifier | Form                              | Role                                                                              |
| ---------- | --------------------------------- | --------------------------------------------------------------------------------- |
| `idp_id`   | short key, e.g. `iam-cern`        | **Canonical** — used in `RseAttr.OIDC_ISSUER` and as `idpsecrets.json` map key    |
| `issuer`   | URL, e.g. `https://iam.cern.ch/`  | Metadata — matched against the `iss` claim of issued tokens; stored inside the IdP entry |

The RSE attribute holds the `idp_id`, not the URL. This avoids ambiguity around trailing slashes, discovery URL aliases, and `iss` claim variations.

**New RSE attribute:** `RseAttr.OIDC_ISSUER` (holds an `idp_id`).

```python
# lib/rucio/common/constants.py
class RseAttr:
    # ... existing attributes ...
    OIDC_SUPPORT = "oidc_support"
    OIDC_ISSUER = "oidc_issuer"  # new — value is an idp_id key
```

**Per-IdP client configuration** in `etc/idpsecrets.json` (map keyed by `idp_id`):

```json
{
  "iam-cern": {
    "issuer": "https://iam.cern.ch/",
    "client_id": "...",
    "client_secret": "...",
    "redirect_uris": ["..."]
  },
  "cilogon": {
    "issuer": "https://cilogon.org/",
    "client_id": "...",
    "client_secret": "..."
  }
}
```

**Extended token-acquisition signature** in `lib/rucio/core/oidc.py`:

```python
def request_token(
    audience: str,
    scope: str,
    idp_id: Optional[str] = None,  # new — falls back to default IdP if None
    use_cache: bool = True,
) -> Optional[str]:
    """Resolve the IdP client config and obtain a scoped access token."""
    idp_config = _resolve_idp_config(idp_id)  # new helper
    # ... existing flow against the resolved IdP ...
```

**Per-RSE issuer resolution** in `lib/rucio/transfertool/fts3.py`:

```python
# In FTS3Transfertool._file_from_transfer
if self.token:
    t_file['source_tokens'] = []
    for source in transfer.sources:
        src_audience = determine_audience_for_rse(rse_id=source.rse.id)
        src_scope = determine_scope_for_rse(
            rse_id=source.rse.id,
            scopes=['storage.read'],
            extra_scopes=['offline_access'],
        )
        src_idp = source.rse.attributes.get(RseAttr.OIDC_ISSUER)  # new — idp_id or None
        t_file['source_tokens'].append(
            request_token(src_audience, src_scope, idp_id=src_idp)
        )

    dst_audience = determine_audience_for_rse(transfer.dst.rse.id)
    dst_scope = determine_scope_for_rse(
        transfer.dst.rse.id,
        scopes=['storage.modify', 'storage.read'],
        extra_scopes=['offline_access'],
    )
    dst_idp = transfer.dst.rse.attributes.get(RseAttr.OIDC_ISSUER)  # new
    t_file['destination_tokens'] = [
        request_token(dst_audience, dst_scope, idp_id=dst_idp)
    ]
```

**Operator workflow:**

```bash
# Tag the source RSE with its trusted IdP (idp_id, not URL)
rucio-admin rse set-attribute SITE_A_DISK \
  --key oidc_issuer --value iam-cern

# Tag the destination RSE with a different IdP
rucio-admin rse set-attribute SITE_B_DISK \
  --key oidc_issuer --value cilogon
```

If `OIDC_ISSUER` is unset on either RSE, that side falls back to the deployment-wide default IdP. Mixed configurations are supported (e.g. tagged source + default destination).

**FTS3-side configuration** (operational, no code change): each FTS3 deployment populates `t_token_provider` with one row per trusted issuer. Existing `t_token.issuer` and `t_token_provider` schema remain unchanged.

### Consequences

* Good, because federated and cross-VO TPC becomes possible without FTS3 schema changes
* Good, because backward compatible — RSEs without `OIDC_ISSUER` fall back to the deployment-wide default
* Good, because per-RSE granularity matches how storage endpoints actually trust issuers
* Good, because failure isolation: if one IdP is unreachable, only RSEs configured against it are affected
* Good, because the `idp_id` indirection makes IdP rotation possible without rewriting RSE attributes (only `idpsecrets.json` changes)
* Bad, because it increases operational surface — each new trusted IdP requires registration in `idpsecrets.json` and a `t_token_provider` row in FTS3
* Bad, because failure mode if one of two IdPs is unreachable mid-transfer — refresh path (FTS3-owned, see Scope Boundary above) must degrade gracefully
* Neutral, because token cache cardinality grows by a factor of N IdPs; existing TTL semantics remain. Per-IdP pool sizing is a tuning concern, not an architectural one.
* Neutral, because the `request_token()` signature is extended additively — existing callers passing only `(audience, scope)` continue to work unchanged.

### Confirmation

* Unit tests in `tests/test_oidc.py` covering per-IdP dispatch, fallback to default, and cache-key isolation between IdPs
* Integration tests in `tests/test_tpc.py` validating cross-IdP TPC submissions using the existing `etc/docker/dev` setup (IndigoIAM + Keycloak)
* **Rollout gate:** promotion from Proposed → Accepted requires passing RFC 8693 token-exchange conformance tests against **at least one non-IAM IdP** (e.g. Keycloak). This addresses the risk that FTS3 token executors carry IAM-flavored assumptions.
* Manual validation against a real federated deployment with two distinct IdPs before production rollout
* Documentation update in `wlcg-tokens.md` describing the per-RSE IdP model

## Pros and Cons of the Options

### Per-RSE issuer attribute on the Rucio side

* Good, because aligns with FTS3's existing per-token issuer model
* Good, because no FTS3 schema migration needed
* Good, because backward compatible via fallback
* Good, because failure-isolated per IdP
* Neutral, because requires extending `request_token()` signature (additive, non-breaking)
* Bad, because operators must register each IdP in `idpsecrets.json` and `t_token_provider`

### Single-IdP federation broker

* Good, because Rucio code stays single-IdP
* Bad, because introduces a new component to deploy, monitor, and secure
* Bad, because creates a single point of failure for all token operations
* Bad, because adds latency to every token request
* Bad, because brokering RFC 8693 between heterogeneous IdPs is itself an unsolved problem

### Per-VO issuer mapping only

* Good, because simpler mental model than per-RSE
* Bad, because doesn't match real-world deployments — same VO often spans RSEs trusting different IdPs
* Bad, because forces VO-wide IdP migration when only one site changes

### Status quo

* Good, because no code changes
* Bad, because blocks federated and cross-VO TPC entirely
* Bad, because forces all sites to trust a single IdP — operationally unrealistic across federations

## More Information

**Cache-key implications:** the existing token cache in `rucio.core.oidc` keys entries by `(audience, scope)`. With per-RSE IdPs, the key must become `(audience, scope, idp_id)` to prevent cross-IdP cache collisions. This is a non-breaking change but must be verified — a stale cache returning a token from the wrong IdP would silently break TPC.

**Files affected (Rucio):**

| File                              | Change                                                            |
| --------------------------------- | ----------------------------------------------------------------- |
| `lib/rucio/common/constants.py`   | Add `RseAttr.OIDC_ISSUER`                                         |
| `lib/rucio/core/oidc.py`          | Add `idp_id=` parameter; per-IdP client dispatch; cache-key fix   |
| `lib/rucio/transfertool/fts3.py`  | Read `RseAttr.OIDC_ISSUER` per RSE in `_file_from_transfer`       |
| `etc/idpsecrets.json` (+template) | Support multiple named IdP entries keyed by `idp_id`              |
| `tests/test_oidc.py`              | Per-IdP dispatch and fallback tests                               |
| `tests/test_tpc.py`               | Cross-IdP TPC integration test                                    |

**Files NOT affected:**
- FTS3 schema (`t_token`, `t_token_provider` already model issuers)
- FTS3 executors at the call-signature level (they already operate on a `Token` carrying its own issuer)
- `url-copy` (unchanged)
- Storage endpoints (unchanged — they already validate against whichever issuer signed the token)

**Migration path for existing deployments:**
1. Deploy the Rucio change with `OIDC_ISSUER` unset on all RSEs → identical behavior to today.
2. Register additional IdPs in `idpsecrets.json` and FTS3's `t_token_provider`.
3. Tag a small set of RSEs with `OIDC_ISSUER` pointing at the new `idp_id`.
4. Run cross-IdP TPC integration tests.
5. Roll out to additional RSEs as confidence grows.

**Open questions (deferred to follow-up ADRs):**
- Behavior when destination-IdP refresh fails mid-transfer while source-IdP refresh succeeds (FTS3-side concern, see Scope Boundary above)
- Token revocation propagation across federated IdPs
- Multi-VO + multi-IdP interaction — whether `t_token_provider.vo_mapping` on FTS3 needs a corresponding Rucio-side concept
- OIDC discovery vs. static config for IdP metadata

**Related:**
- Concept: [`multi-idp-third-party-copy.md`](../8-concepts/multi-idp-third-party-copy.md)
- Runtime view: [`third-party-copy-sequence.md`](../6-runtime-view/third-party-copy-sequence.md)
- Extends: [`adr-004-token-propagation-strategy.md`](./adr-004-token-propagation-strategy.md)
- Background: [`wlcg-tokens.md`](../8-concepts/wlcg-tokens.md)
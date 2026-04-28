# Multi-IdP support for third-party copy

## Context

Third-party copy (TPC) between two storage endpoints requires a bearer token at the source and a bearer token at the destination. Today, both tokens are obtained from the same IdP configured in Rucio. Real-world federated and cross-VO scenarios — e.g. data hosted on a CILogon-trusting endpoint copied to a CERN-IAM-trusting endpoint — require tokens from different issuers in the same transfer.

## Status quo

Rucio (`rucio.transfertool.fts3.FTS3Transfertool._file_from_transfer`) already fetches **separate tokens** for source and destination, with per-RSE `audience` and `scope` resolved via `determine_audience_for_rse` / `determine_scope_for_rse`. However, `request_token()` in `rucio.core.oidc` is bound to a single Rucio-wide IdP configuration — there is no per-RSE issuer selection.

FTS3 is already further along than Rucio:

- `t_token` carries `issuer` as a NOT NULL FK to `t_token_provider`.
- `t_file.src_token_id` and `t_file.dst_token_id` are independent FKs — a single transfer can already be bound to two tokens with two different issuers.
- `TokenExchangeExecutor` and `TokenRefreshExecutor` operate on a `Token` object that carries its own `issuer`; the `tokenEndpointMap` in `TokenHttpExecutor` is keyed by issuer string.
- `t_token_provider` allows per-issuer `client_id`, `client_secret`, `required_submission_scope`, `vo_mapping`.

For the end-to-end sequence, see [`6-runtime-view/third-party-copy-sequence.md`](../6-runtime-view/third-party-copy-sequence.md).

## Gap

The bottleneck is on the submitter side, not the transfer service:

1. **Rucio has no per-RSE issuer.** `request_token(audience, scope)` cannot be told *which* IdP to ask. A new `RseAttr.OIDC_ISSUER` and an `issuer=` parameter on `request_token` are required.
2. **FTS executors may carry IAM-flavored assumptions.** `IAMWorkflowError.h` and adjacent code paths suggest some token-exchange details (grant_type variants, audience claim shape) may need to be generalized for non-IAM IdPs (Keycloak, CILogon, Authlete). To be verified.
3. **Operational config.** Each FTS3 deployment must populate `t_token_provider` with one row per trusted IdP. No schema change needed.

## Desired state

- Rucio admins set `oidc_issuer` per RSE. Default falls back to the existing single-IdP config for backward compatibility.
- `request_token()` dispatches to the correct IdP client config based on the resolved issuer.
- FTS3 receives a job whose source and destination tokens carry distinct `iss` claims; persists them as two `t_token` rows; exchanges and refreshes each against its own issuer.
- `url-copy` hands the right bearer to gfal2 per endpoint, unchanged from today.

For the desired-state sequence, see [`6-runtime-view/third-party-copy-sequence.md`](../6-runtime-view/third-party-copy-sequence.md).

## Open questions

- RFC 8693 conformance across candidate IdPs (token-exchange grant_type, response shape).
- WLCG JWT Profile alignment for all IdPs in scope.
- Revocation and rotation semantics when source and destination issuers differ.
- Failure modes when one of two issuers is unreachable mid-transfer.

## References

- ADR: [`adr-008-multi-idp-token-issuance-per-rse.md`](../9-adrs/adr-008-multi-idp-token-issuance-per-rse.md)
- Runtime view: [`third-party-copy-sequence.md`](../6-runtime-view/third-party-copy-sequence.md)
- Related ADR: [`adr-004-token-propagation-strategy.md`](../9-adrs/adr-004-token-propagation-strategy.md)
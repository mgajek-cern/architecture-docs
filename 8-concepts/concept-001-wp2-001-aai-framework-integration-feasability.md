**DEPRECATED**

## **1. AAI Framework Integration (WP4)**

**Technical Concept:** Multi-issuer federated authentication with fine-grained authorization

**Key Files to Modify:**
- `lib/rucio/core/authentication.py` - Add multi-issuer OIDC token validation
  *// **High complexity** - Current single-issuer JWT validation needs complete rewrite for multiple issuer discovery/validation*
- `lib/rucio/core/identity.py` - Support federated identity mapping
  *// **Medium complexity** - Extend existing identity model but requires new enum types and 1:many mappings*
- `lib/rucio/core/permission/generic.py` - Extend permission model for RI-specific policies
  *// **Very high complexity** - Current simple role-based system incompatible with fine-grained federated policies*
- `lib/rucio/web/rest/flaskapi/v1/auth.py` - Add federated token endpoints
  *// **Medium complexity** - Add new REST endpoints but depends on core authentication changes*
- `lib/rucio/client/baseclient.py` - Support token-based client authentication
  *// **High complexity** - Single auth endpoint assumption breaks; need multi-issuer token management*
- `lib/rucio/db/sqla/models.py` - Add federated identity tables
  *// **Low complexity** - Straightforward table additions but production migration risk*

**New Components Needed:**
- Policy decision point integration module
  *// **Very high complexity** - No existing framework; requires building from scratch*
- Multi-tenant namespace isolation logic
  *// **High complexity** - Current VO model insufficient; need new isolation mechanisms*

**Feasibility Assessment: HIGH RISK**
- **Performance impact:** Multi-issuer validation could add 200-500ms latency per request
- **Architectural mismatch:** Current centralized auth model fundamentally incompatible with federation
- **Backward compatibility:** Risk breaking existing single-issuer deployments
- **Development effort:** Estimated 6-12 months for production-ready implementation
- **Operational complexity:** Trust relationship management between RIs requires new governance processes

**Recommendation:** Consider incremental approach with feature flags or evaluate alternative federation strategies before committing to this architectural change.
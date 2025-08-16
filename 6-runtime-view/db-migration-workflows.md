# Database Migration workflows

## Automatic Migration (Development/CI)
1. *Developer* → *Kubernetes*: `kubectl exec -it rucio-server-pod -- alembic upgrade head`
2. *Alembic (in pod)* → *Database*: Reads current schema version from alembic_version table
3. *Alembic* → *Rucio Migration Scripts* (in pod): Loads pending migration files from `/opt/rucio/lib/rucio/db/sqla/migrate_repo/`
4. *Alembic* → *Database*: Executes Rucio-specific SQL DDL commands
5. *Alembic* → *Database*: Updates alembic_version table
6. **Error path**: Migration fails → *Alembic* → *Developer*: "Migration error" → Manual rollback required

## Manual Migration (Production)
1. *Database Administrator* → *Kubernetes*: `kubectl exec -it rucio-server-pod -- alembic current`
2. *Database Administrator* → *Kubernetes*: `kubectl exec -it rucio-server-pod -- alembic history`
3. *Database Administrator* → *Kubernetes*: `kubectl exec -it rucio-server-pod -- alembic upgrade +1`
4. *Alembic (in pod)* → *Database*: Execute single Rucio migration with validation
5. *Database Administrator*: Verify Rucio functionality before next migration
6. Repeat steps 3-5 until target version reached
7. **Error path**: *Database Administrator* → *Kubernetes*: `kubectl exec -it rucio-server-pod -- alembic downgrade -1`
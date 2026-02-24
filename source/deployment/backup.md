# Backup & Recovery

## What to Back Up

| Directory | Priority | Regeneratable? |
|-----------|----------|---------------|
| `data/` | **Critical** | No - all application data |
| `applications/` | **Critical** | No - configs and source |
| `yeti-config.yaml` | **Important** | No - server configuration |
| `certs/` | Important | Yes if `autoGenerate: true` |
| `cache/builds/` | Low | Yes - recompiled on startup |

## Embedded Mode Backup

RocksDB supports hot backup - safe to copy while server is running:

```bash
BACKUP_DIR="/backups/yeti-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r /var/lib/yeti/data "$BACKUP_DIR/data"
cp -r /var/lib/yeti/applications "$BACKUP_DIR/applications"
cp /var/lib/yeti/yeti-config.yaml "$BACKUP_DIR/"
```

Incremental with rsync:

```bash
rsync -av --delete /var/lib/yeti/data/ /backups/yeti-latest/data/
rsync -av --delete /var/lib/yeti/applications/ /backups/yeti-latest/applications/
```

### Automated Backups

```yaml
maintenance:
  backup:
    enabled: true
    intervalHours: 24
    retentionDays: 30
```

## Cluster Mode Backup

Application data lives in the distributed cluster. The Yeti server itself is stateless - back up only `applications/` and `yeti-config.yaml`. Back up cluster node data volumes separately.

## Recovery

### Full Recovery (Embedded)

```bash
yeti stop
cp -r /backups/yeti-latest/data /var/lib/yeti/data
cp -r /backups/yeti-latest/applications /var/lib/yeti/applications
cp /backups/yeti-latest/yeti-config.yaml /var/lib/yeti/
yeti start --root-dir /var/lib/yeti
```

Plugin cache regenerates automatically (~2 min per plugin).

### Partial Recovery (Single Database)

```bash
yeti stop
rm -rf /var/lib/yeti/data/my-app
cp -r /backups/yeti-latest/data/my-app /var/lib/yeti/data/my-app
yeti start --root-dir /var/lib/yeti
```

### Rebuilding Plugin Cache

After recovery or Yeti upgrade:

```bash
rm -rf /var/lib/yeti/cache/builds/*/target/
rm -rf /var/lib/yeti/cache/builds/*/src/
yeti start --root-dir /var/lib/yeti
```

## Disaster Recovery

### Embedded Mode

- **RTO**: ~5 minutes (copy data + plugin recompile)
- **RPO**: Depends on backup frequency
- No cross-architecture restore (x86 backups cannot restore on ARM)

### Cluster Mode

- Single node failure causes no data loss (3+ replicas)
- Only `applications/` and `yeti-config.yaml` need restoring on the Yeti server

## Verify Backups

```bash
yeti start --root-dir /backups/yeti-latest --apps yeti-auth
curl -sk https://localhost:9996/yeti-auth/auth
```

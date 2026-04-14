# Backup & Recovery

## What to Back Up

| Directory | Priority | Regeneratable? |
|-----------|----------|---------------|
| `data/` | **Critical** | No - all application data |
| `applications/` | **Critical** | No - configs and source |
| `yeti-config.yaml` | **Important** | No - server configuration |
| `certs/` | Important | Yes if `autoGenerate: true` |
| `cache/builds/` | Low | Yes - recompiled on startup |

## Backup Procedure

RocksDB supports hot backup -- safe to copy while the server is running:

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

Use cron or systemd timers to schedule backup scripts:

```bash
# Example crontab entry: daily backup at 2 AM
0 2 * * * /usr/local/bin/yeti-backup.sh
```

## Recovery

### Full Recovery

```bash
# Stop the server, restore data, restart
cp -r /backups/yeti-latest/data /var/lib/yeti/data
cp -r /backups/yeti-latest/applications /var/lib/yeti/applications
cp /backups/yeti-latest/yeti-config.yaml /var/lib/yeti/
# Restart yeti - plugin cache regenerates automatically (~2 min per plugin)
```

### Partial Recovery (Single Database)

```bash
rm -rf /var/lib/yeti/data/my-app
cp -r /backups/yeti-latest/data/my-app /var/lib/yeti/data/my-app
# Restart yeti
```

### Rebuilding Plugin Cache

After recovery or Yeti upgrade:

```bash
rm -rf /var/lib/yeti/cache/builds/*/target/
rm -rf /var/lib/yeti/cache/builds/*/src/
yeti start --dir /var/lib/yeti
```

## Replication as Durability Strategy

For durability beyond backups, enable replication across multiple nodes:

```yaml
replication:
  enabled: true
  port: 9997
  seedNodes:
    - "peer1:9997"
    - "peer2:9997"
```

Replication is license-gated. See [Storage Engine](../architecture/storage.md) for details.

## Disaster Recovery

- **RTO**: ~5 minutes (copy data + plugin recompile)
- **RPO**: Depends on backup frequency (or near-zero with replication)
- No cross-architecture restore (x86 backups cannot restore on ARM)

## Verify Backups

```bash
yeti start --dir /backups/yeti-latest --apps yeti-auth
curl -sk https://localhost:9996/yeti-auth/auth
```

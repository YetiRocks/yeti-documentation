# Production Checklist

## TLS Certificates (Required)

Replace self-signed certificates with real ones:

```yaml
tls:
  autoGenerate: false
  privateKey: "/etc/yeti/tls/private.key"
  certificate: "/etc/yeti/tls/certificate.pem"
```

## Environment Variables (Required)

```bash
export JWT_SECRET_KEY="your-production-secret-min-32-chars"
export GITHUB_CLIENT_ID="..."
export GITHUB_CLIENT_SECRET="..."
export ENVIRONMENT="production"
```

## Storage (Required)

### Embedded Mode

```yaml
storage:
  mode: embedded
  path: "/var/lib/yeti/data"
  caching: true
  compression: true
```

Use SSDs. Set up regular backups (see [Backup & Recovery](backup.md)).

### Cluster Mode

```yaml
storage:
  mode: cluster
  cluster:
    pdEndpoints: ["pd1:23791", "pd2:23792", "pd3:23793"]
    tlsCaPath: /etc/yeti/tls/ca.pem
    tlsCertPath: /etc/yeti/tls/client.pem
    tlsKeyPath: /etc/yeti/tls/client-key.pem
    autoStart: false
```

Provision 3+ PD nodes and 3+ storage nodes. Enable mTLS in production.

## Logging

```yaml
logging:
  level: "warn"
  auditLog: true
```

## CORS

```yaml
http:
  cors: true
  corsAccessList:
    - "https://app.yourdomain.com"
```

Never use `"*"` in production.

## Operations API

```yaml
operationsApi:
  enabled: true
  requireAuth: true
  cors: false
```

Bind to localhost or restrict with firewall rules.

## Application Review

- Remove or disable unused example applications
- Verify OAuth rules per extension config
- Check that seed data is appropriate for production
- Ensure `app_id` values are stable (changing breaks client URLs)

## Set Environment to Production

```yaml
environment: "production"
```

Enables SSRF validation and stricter security defaults.

## Post-Deployment

```bash
curl -s https://your-server:9995/health
curl -v https://your-server:443/documentation/ 2>&1 | grep "SSL certificate"
```

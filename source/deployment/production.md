# Production Checklist

## TLS Certificates (Required)

Replace self-signed certificates with production certificates:

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

```yaml
storage:
  mode: embedded
  path: "/var/lib/yeti/data"
  caching: true
  compression: true
```

Use SSDs. Configure regular backups (see [Backup & Recovery](backup.md)).

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

Do not use `"*"` in production.

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
curl -sk https://your-server:9996/health
curl -v https://your-server:9996/documentation/ 2>&1 | grep "SSL certificate"
```

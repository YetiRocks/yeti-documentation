# Resource Hooks

Hooks are shell commands that run before or after resource handler execution. Use them for validation gates, audit logging, and failure alerting without modifying handler code.

## Configuration

Add hooks to your application's `config.yaml`:

```yaml
hooks:
  pre_request:
    - "./hooks/validate.sh"
    - "./hooks/rate-check.sh"
  post_request:
    - "./hooks/audit-log.sh"
  post_request_failure:
    - "./hooks/alert.sh"
```

## Hook Events

| Event | When | Can deny? | Use case |
|-------|------|-----------|----------|
| `pre_request` | Before handler runs | Yes (exit 2) | Validation, rate limiting, IP filtering |
| `post_request` | After successful response | No | Audit logging, metrics, webhooks |
| `post_request_failure` | After error response | No | Alerting, error tracking |

## Input

Each hook receives a JSON object on stdin:

```json
{
  "event": "pre_request",
  "method": "POST",
  "path": "/my-app/api/orders",
  "app_id": "my-app",
  "resource": "orders",
  "identity": {
    "username": "alice",
    "role": "admin"
  }
}
```

Post-request hooks also receive:

```json
{
  "event": "post_request",
  "status": 200,
  "latency_ms": 12
}
```

## Exit Code Protocol

For `pre_request` hooks only:

| Exit code | Meaning |
|-----------|---------|
| `0` | Allow — continue to handler |
| `2` | Deny — return 403 Forbidden |
| Any other | Allow — hook failure doesn't block the request |

Post-request hooks are fire-and-forget. Exit codes are ignored.

## Example: IP Allowlist

```bash
#!/bin/bash
# hooks/validate.sh — deny requests from unknown IPs
INPUT=$(cat)
IP=$(echo "$INPUT" | jq -r '.identity.ip // "unknown"')

if ! grep -q "$IP" ./hooks/allowlist.txt 2>/dev/null; then
  exit 2  # deny
fi
```

## Example: Audit Log

```bash
#!/bin/bash
# hooks/audit-log.sh — append to JSONL audit file
cat >> ./logs/audit.jsonl
```

## Execution

- Hooks run sequentially in the order listed
- Pre-request hooks stop on first denial (exit 2)
- Post hooks run in parallel, fire-and-forget
- Hook timeout: inherits the application's `request_timeout`
- Hook failures are logged but never crash the server

## See Also

- [Application Configuration](../reference/app-config.md) — `hooks:` section reference
- [Custom Resources](custom-resources.md) — Handler code that hooks wrap

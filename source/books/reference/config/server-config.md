# Server Configuration

`yeti-config.yaml` at the root directory (default
`~/yeti/yeti-config.yaml`). Override only what you need — every field
has a default.

A `.env` file in the root directory is loaded on startup; real
environment variables take precedence. The root directory itself is
set in `~/.yeti/settings.toml`, not here.

## Default — every field commented

```yaml
# ─── Environment ─────────────────────────────────────────────────────
environment: development          # development | production
# rootApp: null                   # App ID that serves at "/" instead of "/{appId}/"

# ─── Interfaces ──────────────────────────────────────────────────────
# All protocols share the main port except MQTT.
# Global enabled: false cannot be overridden by @export.
interfaces:
  port: 9996                      # Main HTTPS (REST, GraphQL, WS, SSE, gRPC, MCP)
  rest:    { enabled: true,  audit: false }
  graphql: { enabled: true,  audit: false }
  ws:      { enabled: true,  audit: false }
  sse:     { enabled: true,  audit: false }
  grpc:    { enabled: true,  audit: false }
  mcp:     { enabled: true,  audit: true }   # MCP audit on by default
  mqtt:
    enabled: true
    audit: false
    port: 8883                    # MQTTS native TLS (separate port)
    max_clients: 10000
    qos: 2                        # Default QoS for bridge-published messages

# ─── HTTP ────────────────────────────────────────────────────────────
http:
  cors: true
  corsAccessList: ["*"]
  timeout: 60000                  # ms
  keepAliveTimeout: 75000
  disconnectTimeout: 5000         # graceful shutdown wait for in-flight
  maxConnectionRate: 256          # new TCP/s
  maxInFlightRequests: 10000      # 503 when exceeded
  compressionThreshold: 1024      # bytes — gzip above this
  maxQueryDepth: 50               # FIQL nesting
  maxQueryConditions: 200         # per query
  maxResultSetSize: 10000         # per scan/list
  maxRequestBodyBytes: 10485760   # 10 MB

# ─── Storage ─────────────────────────────────────────────────────────
# Sharded RocksDB; per-table overrides via @store.
storage:
  caching: true
  compression: true               # LZ4 on-disk
  # path: null                    # default {rootDirectory}/data/
  # cacheSizeMb: 2048
  # writeBufferSizeMb: 512
  # shardCount: null              # default num_cpus / 2 (min 2)
  # inMemory: false               # volatile, no disk

# ─── Replication ─────────────────────────────────────────────────────
# License-gated. Omit entirely for standalone. See architecture/replication.md.
replication:
  enabled: false
  # licenseKey: null
  port: 9997                      # gRPC (TCP) + chitchat gossip (UDP), same port
  # seedNodes: ["peer1:9997", "peer2:9997"]
  # advertiseAddr: ""
  # nodeId: null
  # region: ""

# ─── Logging ─────────────────────────────────────────────────────────
# Core writes stdout only; file logging owned by yeti-telemetry.
logging:
  level: info                     # trace | debug | info | warn | error
  # path: null                    # default {rootDirectory}/logs/

# ─── Applications ────────────────────────────────────────────────────
applications:
  # path: null                    # default {rootDirectory}/applications/
  autoLoad: []                    # Git repos to clone on startup

# ─── Threads ─────────────────────────────────────────────────────────
threads:
  # count: null                   # default CPU count
  debug: false

# ─── TLS ─────────────────────────────────────────────────────────────
tls:
  autoGenerate: true              # self-signed when missing
  domain: localhost
  # privateKey: null              # PEM path
  # certificate: null             # PEM path

# ─── Rate limiting ───────────────────────────────────────────────────
rateLimiting:
  maxRequestsPerSecond: 1000      # server-wide; per-app via yeti-ratelimit

# ─── Telemetry ───────────────────────────────────────────────────────
telemetry:
  metrics: true
  serviceName: yeti
  # otlpEndpoint: "http://otel:4317"
  metricsIntervalSecs: 10

# ─── Object store (S3-compatible; falls back to {rootDirectory}/object-store/) ──
rustfs:
  enabled: false
  endpoint: "http://localhost:9000"
  accessKey: minioadmin
  secretKey: minioadmin

# ─── Environment variables (injected at startup) ─────────────────────
env: {}

# ─── Plugins ─────────────────────────────────────────────────────────
plugins:
  yeti-auth:
    enabled: true
    jwt:
      secret: "development-secret-change-in-production"
      algorithm: HS256
      accessTtl: 900              # 15 min
      refreshTtl: 604800          # 7 days
    oauth:
      github:    { clientId: "", clientSecret: "" }
      google:    { clientId: "", clientSecret: "" }
      microsoft: { clientId: "", clientSecret: "" }
  yeti-telemetry: { enabled: true }
  yeti-ai:        { enabled: true }

# Top-level `auth:` is shorthand parsed into plugins.yeti-auth.

# ─── Management ──────────────────────────────────────────────────────
# Who holds the node admin role, yeti_admin. The install username and
# password always do. An OAuth identity does only when a rule here
# matches what its provider verified; with no rules, none does.
# Rules are read at start: a change takes effect on restart.
# management:
#   admin:
#     oauth:
#       rules:
#         - { provider: google, claims: "hd=example.com" }
#         - { provider: github, email: "ops@example.com" }
```

`management.admin.oauth.rules` keys:

- `provider`: the provider's type, `google`, `github` or `microsoft`.
- `email`: one address, or `*@domain` with the provider's proof of the domain (below), matched
  only against an email the provider verified, or on a `tid`-pinned Microsoft rule the member's
  UPN (below). Case doesn't matter; a trailing dot or a space in
  the domain is refused.
- `claims`: `field=value`, or `field` for a present, true claim. A string or number value
  compares as text, so GitHub's `id=583231` matches; an array or boolean claim never matches. `hd`,
  `tid` and `oid` compare without case.
- `allow_any_account`: `true` lets a rule that can't narrow below a whole provider load.

Every key a rule names must match. App rules in `[package.metadata.auth.oauth]` can't grant
`yeti_admin`, and neither can a WebAssembly auth provider, whose sign-in reaches the node as a JWT.

A rule must narrow below a whole provider, with an exact address, or a claim whose field names
one account or organisation of that provider:

| `provider` | Claim fields that narrow |
|---|---|
| `google` | `hd`, `email`, `sub` |
| `github` | `id`, `email` |
| `microsoft` | `tid`, `oid`, `sub`, `email` |
| any other type | `email` |
| none named | no claim; an exact `email` address only |

Any other field narrows nothing, since every account of the provider carries it (`iss`, `aud`,
`azp`, `email_verified`, GitHub's `type: User`) or its holder can set it. GitHub's `login` is left
out because a renamed login is free for anyone to register; use `id`. The `tid` of personal
Microsoft accounts, `9188040d-6c67-4c5b-b112-36a304b66dad`, fails load, and so does any `tid`
that is not a tenant GUID: `common`, `organizations`, `consumers`, a wildcard or a padded value.
A provider
type other than `google`, `github` or `microsoft` is a name the operator chose, and `sub`, a tenant
or a group is unique only within one issuer, so such a type narrows only on `email`.

A domain rule, `email: "*@example.com"`, loads only with the provider's proof that the account
belongs to that domain's organisation:

- `provider: google` with `claims: "hd=example.com"`, the same domain. Google sets `hd` only on a
  Workspace account, so a personal Google account registered on a company address never matches.
- `provider: microsoft` with `claims: "tid=<tenant GUID>"`, a work tenant, never the
  personal-account tenant above.

A Microsoft rule that names a `tid`, with or without an email, admits members of that tenant
only, and only when the signed token's `tid` and issuer are that tenant's. Guests never match: a
token whose `idp` differs from its `iss`, whose `acct` is not `0`, or whose `upn` or
`preferred_username` holds `#EXT#` is refused, even when another claim says member. Entra ID
tokens carry no `email_verified`, so the address such a rule matches is the member's UPN, `upn`,
else `preferred_username`, whose domain the tenant has verified; the token's `email` is never
read, since Microsoft sends it unverified and a guest's `email` is the guest's own. The same
address from another tenant or from a personal account never matches. A Microsoft email rule with no `tid` pin matches
only a token that carries `email_verified: true`; Google and GitHub rules always need a verified
email.

On GitHub, Apple or any other provider type, anyone may verify an address at a domain, a public
mail domain or a relay domain included, so a domain rule there fails load unless it sets
`allow_any_account: true`. With no provider it fails load outright. An exact address, such as
`ops@gmail.com`, always loads.

A rule that narrows nothing, whether it names only a provider, `email: "*"`, a wildcard domain such
as `*@*`, a domain rule without the provider's proof, a bare claim name such as `sub`, or a claim
field not in the table, would make every account of that provider the node admin, so it fails
config load naming the rule's
index, the field or domain, and how to narrow it. To admit every account of one provider on
purpose, add `allow_any_account: true` and a `provider`; the node logs a warning naming the rule at
every start. A misspelt key under `management:` also fails load.

Prefer exact addresses, or `hd=` for Google Workspace. GitHub marks an address verified once and
doesn't check it again after its owner leaves, which is why a GitHub domain rule needs the opt-in. On
GitHub, `claims` reads the user's profile, which the account holder edits; `company`, `name`,
`blog` and `bio` prove nothing, while `id` is fixed for the account.

Rules are read once, at start. Adding or removing one takes effect when the node restarts; until
then an admin whose rule was removed stays admin, and every request is checked against the rules the
node started with.

## Modes — `environment`

| Value | Auth | Logging | TLS |
|---|---|---|---|
| `development` | Bypasses auth for user-defined apps | `info` default | Self-signed OK |
| `production` | Enforces auth on all routes | `warn` default | Real certs expected |

## Tuning notes

- **Read-heavy:** raise `storage.cacheSizeMb`.
- **Write-heavy:** raise `storage.writeBufferSizeMb` and `storage.shardCount`.
- **Ephemeral data:** `storage.inMemory: true` (or per-table `@store(durability: "memory")`).
- **I/O-bound app:** `threads.count` ≈ 2× CPU count.
- **CPU-bound (vector embeds, inference):** lower `threads.count` to leave cores free.
- **Production telemetry:** raise `telemetry.metricsIntervalSecs` to 30–60.
- **Production auth:** real `tls.certificate` / `tls.privateKey`, `tls.autoGenerate: false`. JWT `accessTtl` ≤ 300 s with refresh rotation.

## Environment overrides

| Variable | Overrides |
|---|---|
| `APPLICATION_PORT` | `interfaces.port` |
| `LOG_LEVEL` | `logging.level` |
| `ENVIRONMENT` | `environment` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `telemetry.otlpEndpoint` |
| `REPLICATION_PORT` | `replication.port` (also enables replication) |
| `SEED_NODES` | `replication.seedNodes` (comma-separated) |

## Production example

```yaml
environment: production
rootApp: www

interfaces:
  port: 443

http:
  cors: false
  corsAccessList: ["https://app.example.com"]
  timeout: 30000
  maxInFlightRequests: 50000
  maxResultSetSize: 5000

storage:
  cacheSizeMb: 8192
  writeBufferSizeMb: 1024
  shardCount: 8

logging: { level: warn }

tls:
  autoGenerate: false
  domain: api.example.com
  privateKey: certs/api.example.com-key.pem
  certificate: certs/api.example.com-cert.pem

telemetry:
  serviceName: yeti-prod
  otlpEndpoint: "http://otel-collector:4317"
  metricsIntervalSecs: 30

plugins:
  yeti-auth:
    jwt:
      secret: "${JWT_SECRET}"
      accessTtl: 300
    oauth:
      github:
        clientId: "${GITHUB_CLIENT_ID}"
        clientSecret: "${GITHUB_CLIENT_SECRET}"

env:
  JWT_SECRET: "loaded-from-env-or-dotenv"
```

## See also

- [Application Configuration](app-config.md) — `[package.metadata.app]` per-app surface
- [Schema Directives](schema-directives.md) — `@store`, `@access`, `@source`, …
- [Replication](../architecture/replication.md) — cluster setup detail

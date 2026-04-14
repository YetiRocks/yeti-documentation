# Yeti Cloud

Managed hosting for Yeti applications. Same binary and SDK as local development -- apps deploy without modification.

## How It Works

Every server in the fleet runs one Yeti instance with four internal applications for routing, builds, process management, and administration. Your applications run as separate Yeti processes, each isolated with its own data directory and resource limits.

### Development to Production

Workflow:

1. **Develop locally** — build your app with `yeti start` on your machine
2. **Deploy** — push source via `yeti deploy` or connect a GitHub repository
3. **Build** — the cloud build server compiles your plugins into `.dylib` files
4. **Distribute** — compiled artifacts replicate to all nodes automatically
5. **Run** — your app starts as an isolated process, accessible via HTTPS

```
Local development:                    Cloud production:
~/yeti/                               Managed infrastructure
├── yeti-config.yaml                  ├── Your app process (isolated)
├── applications/                     │   ├── config.yaml
│   └── my-api/                       │   ├── schema.graphql
│       ├── config.yaml               │   ├── compiled plugins (.dylib)
│       ├── schema.graphql            │   └── data/ (own RocksDB)
│       └── resources/*.rs            └── HTTPS endpoint
└── data/
```

Source compiles remotely. Only plugin binaries, configuration, schema, and static assets reach production servers.

## Deployment

### Connected Repository (Recommended)

Connect a GitHub repository for automatic deployments on push:

1. Navigate to **Deployments > Connect Repository** in Studio
2. Authenticate with GitHub and select your repository
3. Yeti Cloud installs a webhook and detects your `yeti-deploy.yaml` manifest
4. Every push to `main` triggers a build and deploy automatically

Branch deploys: push to a feature branch for a preview at `{app}--{branch}.{customer}.dev.cloud.yetirocks.com`.

### CLI Deploy

Deploy directly from your local machine:

```bash
# Deploy all apps in the manifest
yeti deploy

# Deploy a single app
yeti deploy --app api

# Check deployment status
yeti deploy status

# Rollback to the previous version
yeti deploy rollback

# Stream logs
yeti deploy logs --app api --follow
```

Reads `yeti-deploy.yaml` from project root, packages source (respecting `.gitignore` and `.yetiignore`), and uploads to the build server.

### Deployment Manifest

`yeti-deploy.yaml` in the repository root defines builds and deployment:

```yaml
# yeti-deploy.yaml
name: acme-platform
customer_id: acme-corp

applications:
  # Apps with source in this repo
  - path: ./apps/api
  - path: ./apps/dashboard

  # Apps from external repos
  - repo: https://github.com/acme-corp/webhooks-app.git
    branch: main

extensions:
  - repo: https://github.com/acme-corp/custom-auth-hook.git

build:
  yeti_version: "0.4"
  profile: production
  target: x86_64-unknown-linux-gnu

deploy:
  api:
    latency_ms: 500
    cpu_limit: 2000m
    memory_limit: 512Mi
  dashboard:
    latency_ms: 1000
    cpu_limit: 1000m
    memory_limit: 256Mi
```

The `latency_ms` target drives regional placement -- lower targets mean more regions.

## Customer Instances

Each application runs as a separate OS process:

- **Process isolation** -- one crash cannot affect other apps or the platform
- **Own RocksDB** -- per-app data directory, persists across deploys and restarts
- **Resource limits** -- CPU, memory, and I/O capped via cgroup v2
- **No network exposure** -- apps communicate via Unix domain sockets, not TCP
- **Subdomain routing** -- traffic at `{app}.{customer}.cloud.yetirocks.com`

All traffic flows through the HTTPS gateway (port 443), routing by `Host` header to Unix sockets. Apps never bind network ports.

## Multi-Region Support

### Automatic Placement

Apps place across regions based on `latency_ms` in the deployment manifest:

| Latency Target | Typical Coverage |
|----------------|-----------------|
| 500ms          | 5+ regions worldwide |
| 1000ms         | 3 regions (baseline) |
| 2000ms         | 1 region |

Paid plans start with three regions (`us-west`, `us-east`, `eu-west`). The auto-scaler expands based on traffic patterns.

### Data Residency

By default, full replication -- every region has a complete copy:

- Reads are always local
- Writes replicate asynchronously
- Last-writer-wins conflict resolution via hybrid logical clocks

For datasets >10GB, sharded replication partitions data across a subset of nodes.

### Multi-Cloud

Runs across multiple providers (Linode, GCP, AWS). Apps run identically on any provider. All inter-node communication uses mTLS regardless of provider boundaries.

## Auto-Scaling

The auto-scaler adjusts capacity based on:

1. **Request latency** — if p95 latency exceeds your SLA target, scale out to closer regions
2. **CPU utilization** — if CPU exceeds 80% for 10 minutes, add instances
3. **Connection saturation** — if connections exceed 80% of capacity, add instances
4. **Underutilization** — if resources are idle for 1 week, scale down

### Scaling Proposals

Topology changes (adding or removing regions) go through a proposal system. Proposals accumulate confidence based on sustained traffic:

- Proposals appear in Studio with evidence (traffic data, latency impact, cost change)
- Approve immediately or let them auto-execute when confidence is high
- Emergency SLA breaches trigger automatic scaling regardless
- Scale-down requires 1-week minimum observation

Within-region scaling happens automatically without proposals.

## Monitoring and Observability

### Built-In Dashboard

Built-in dashboard in Studio. Charts update via SSE (30-second interval):

- Request rate and error rate
- Latency percentiles (p50, p95, p99)
- CPU and memory utilization per instance
- Storage and network I/O
- Active connections
- Cost accumulation

### OTLP Export

Connect existing observability tools (Grafana, Datadog, New Relic) via OTLP export:

```
https://{app}.{customer}.cloud.yetirocks.com/otel/v1/metrics
https://{app}.{customer}.cloud.yetirocks.com/otel/v1/traces
https://{app}.{customer}.cloud.yetirocks.com/otel/v1/logs
```

### Log Access

Logs are per-instance. Drill into specific instances via Studio (region, app, instance). For cross-instance aggregation, configure OTLP export.

### Data Retention

- Real-time metrics: 30 days
- Aggregated usage data: 13 months
- Logs and spans: 30 days per instance
- For longer retention, configure OTLP export

## Self-Hosted vs. Cloud

| | Self-Hosted | Yeti Cloud |
|---|---|---|
| **Binary** | Same Yeti binary | Same Yeti binary |
| **SDK** | Same yeti-sdk | Same yeti-sdk |
| **Applications** | Identical config.yaml, schema.graphql, resources/*.rs | Identical |
| **Storage** | RocksDB (you manage) | RocksDB (managed, isolated per app) |
| **Deployment** | Manual (SCP, CI/CD) | `yeti deploy` or git push |
| **Scaling** | Manual | Automatic, latency-driven |
| **Replication** | Requires license key | Built-in, managed |
| **Multi-region** | You provision servers | Automatic placement |
| **TLS** | You manage certificates | Managed via Cloudflare |
| **Monitoring** | yeti-telemetry (self-managed) | Built-in dashboard + OTLP export |
| **Cost** | Your infrastructure costs | Usage-based pricing |

Same platform locally and in the cloud. App code, configuration, and schemas are identical. The cloud adds managed infrastructure, automatic scaling, and multi-region distribution.

## Version Management

Multiple binary versions run simultaneously. Pin a major version in the manifest:

```yaml
build:
  yeti_version: "0.4"
```

- **Patch updates** (0.4.2 to 0.4.3) -- applied automatically
- **Minor updates** (0.4.x to 0.4.y) -- applied automatically
- **Major updates** (0.4.x to 0.5.0) -- opt-in; test locally first, then update your manifest

## Getting Started

1. Sign up at [cloud.yetirocks.com](https://cloud.yetirocks.com) (Google/GitHub OAuth or email)
2. Install the Yeti CLI: `curl -fsSL https://yetirocks.com/install.sh | sh`
3. Create your app: `yeti init my-api`
4. Develop locally: `yeti start`
5. Deploy: `yeti deploy`

No credit card is required for the free tier (1 app, 1 region, limited resources).

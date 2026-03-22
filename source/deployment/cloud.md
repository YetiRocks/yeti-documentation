# Yeti Cloud

Yeti Cloud is a managed hosting platform for Yeti applications. It runs the same Yeti binary and SDK you use locally — your apps deploy to the cloud without modification.

## How It Works

Yeti Cloud is itself a Yeti deployment. Every server in the fleet runs one Yeti instance with four internal applications that handle routing, builds, process management, and administration. Your applications run as separate Yeti processes on the same infrastructure, each isolated with its own data directory and resource limits.

### Development to Production

The workflow from local development to cloud deployment:

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

Your source code is compiled remotely. Only the resulting plugin binaries, configuration, schema, and static assets are deployed to production servers. Source files are never shipped to cloud servers.

## Deployment

### Connected Repository (Recommended)

Connect your GitHub repository for automatic deployments on push:

1. Navigate to **Deployments > Connect Repository** in Studio
2. Authenticate with GitHub and select your repository
3. Yeti Cloud installs a webhook and detects your `yeti-deploy.yaml` manifest
4. Every push to `main` triggers a build and deploy automatically

Branch deploys are also supported — push to a feature branch and get a preview deployment at `{app}--{branch}.{customer}.dev.cloud.yetirocks.com`.

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

The CLI reads `yeti-deploy.yaml` from your project root, packages source (respecting `.gitignore` and `.yetiignore`), and uploads it to the build server.

### Deployment Manifest

The `yeti-deploy.yaml` file in your repository root defines what gets built and how it deploys:

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

The `latency_ms` target drives regional placement — lower latency targets result in more regions and better global coverage.

## Customer Instances

Each deployed application runs as a separate operating system process with full isolation:

- **Process isolation** — one app crashing cannot affect other apps or the platform
- **Own RocksDB** — each app has its own data directory that persists across deploys and restarts
- **Resource limits** — CPU, memory, and I/O are capped per instance via cgroup v2
- **No network exposure** — apps communicate with the platform via Unix domain sockets, not TCP ports
- **Subdomain routing** — traffic reaches your app at `{app}.{customer}.cloud.yetirocks.com`

All inbound traffic flows through the platform's HTTPS gateway (port 443), which routes requests by `Host` header to the appropriate app via its Unix socket. Your app never binds a network port.

## Multi-Region Support

### Automatic Placement

Yeti Cloud places your app across regions based on the `latency_ms` target in your deployment manifest. Lower latency targets mean more regions:

| Latency Target | Typical Coverage |
|----------------|-----------------|
| 500ms          | 5+ regions worldwide |
| 1000ms         | 3 regions (baseline) |
| 2000ms         | 1 region |

Paying customers receive a baseline topology of three regions: `us-west`, `us-east`, and `eu-west`. The auto-scaler expands beyond this based on traffic patterns.

### Data Residency

By default, all instances of your app share the same data via full replication — every region has a complete copy. This means:

- Reads are always local (no cross-region queries)
- Writes replicate asynchronously to all regions
- Conflict resolution uses last-writer-wins with hybrid logical clocks

For apps with large datasets (>10GB), sharded replication is available, where data is partitioned and only stored on a subset of nodes.

### Multi-Cloud

Yeti Cloud runs across multiple cloud providers (Linode, GCP, AWS). The platform is provider-agnostic — your app runs identically on any provider. All inter-node communication uses mTLS encryption regardless of provider boundaries.

## Auto-Scaling

The auto-scaler monitors your app continuously and adjusts capacity based on:

1. **Request latency** — if p95 latency exceeds your SLA target, scale out to closer regions
2. **CPU utilization** — if CPU exceeds 80% for 10 minutes, add instances
3. **Connection saturation** — if connections exceed 80% of capacity, add instances
4. **Underutilization** — if resources are idle for 1 week, scale down

### Scaling Proposals

Topology changes (adding or removing regions) go through a proposal system rather than executing immediately. Proposals accumulate confidence points over time based on sustained traffic patterns:

- Proposals appear in the Studio UI with evidence (traffic data, latency impact, cost change)
- You can approve proposals immediately or let them auto-execute when confidence is high
- Emergency SLA breaches trigger automatic scaling regardless of proposal status
- Scale-down proposals require a 1-week minimum observation period

Within-region scaling (adding instances to an existing region) happens automatically without proposals.

## Monitoring and Observability

### Built-In Dashboard

Every Yeti Cloud app includes a monitoring dashboard accessible from Studio. Charts update in real-time via SSE (30-second push interval):

- Request rate and error rate
- Latency percentiles (p50, p95, p99)
- CPU and memory utilization per instance
- Storage and network I/O
- Active connections
- Cost accumulation

### OTLP Export

Connect your existing observability tools (Grafana, Datadog, New Relic) by configuring an OTLP export endpoint. Your app exposes standard OpenTelemetry Protocol endpoints:

```
https://{app}.{customer}.cloud.yetirocks.com/otel/v1/metrics
https://{app}.{customer}.cloud.yetirocks.com/otel/v1/traces
https://{app}.{customer}.cloud.yetirocks.com/otel/v1/logs
```

### Log Access

Logs are stored per-instance. Use Studio to drill into a specific instance's logs (region, app, then instance). For centralized cross-instance log aggregation, configure OTLP export to a third-party log service.

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

The key principle: Yeti Cloud runs the exact same platform you run locally. Your app code, configuration, and schemas are identical. The cloud adds managed infrastructure, automatic scaling, and multi-region distribution.

## Version Management

Yeti Cloud supports multiple binary versions simultaneously. Your deployment manifest pins a major version:

```yaml
build:
  yeti_version: "0.4"
```

- **Patch updates** (0.4.2 to 0.4.3) — applied automatically, no action needed
- **Minor updates** (0.4.x to 0.4.y) — applied automatically, new features available
- **Major updates** (0.4.x to 0.5.0) — opt-in; test locally first, then update your manifest

When a new major version is available, Studio shows a notification. Update your local Yeti binary, test your apps, then update `yeti_version` in your manifest and deploy.

## Getting Started

1. Sign up at [cloud.yetirocks.com](https://cloud.yetirocks.com) (Google/GitHub OAuth or email)
2. Install the Yeti CLI: `curl -fsSL https://yetirocks.com/install.sh | sh`
3. Create your app: `yeti init my-api`
4. Develop locally: `yeti start`
5. Deploy: `yeti deploy`

No credit card is required for the free tier (1 app, 1 region, limited resources).

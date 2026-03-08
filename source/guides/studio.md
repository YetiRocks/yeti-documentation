# Studio

Studio is Yeti's built-in administration UI. Access it at `https://localhost:9996/admin`.

## Applications

The Applications tab lists all installed apps with their status, resource count, and table count.

### Managing an Application

Click **Manage** to open an application. Three tabs are available:

**Code** - File browser with syntax-highlighted source viewer. Markdown files render automatically. The README opens by default.

**Data** - Browse table contents with a left sidebar for navigation. Edit records inline with the JSON editor. Delete records with confirmation.

**Config** - View the application's `config.yaml` as syntax-highlighted JSON.

### Installing Applications

Click **New Application** to install from:

- **Demo apps** - Pre-built examples from the yetiRocks GitHub organization
- **Git repository** - Paste any repository URL to clone and install
- **Local directory** - Create manually in `~/yeti/applications/`

After installation, the app compiles (~2 minutes first time) and starts serving.

### Deleting Applications

Click **Delete** on any application in the list. A confirmation dialog prevents accidental removal. Built-in extensions (yeti-auth, yeti-telemetry, yeti-vectors) cannot be deleted.

## Telemetry

The Telemetry tab provides real-time observability:

**Logs** - Live log stream with level filtering (TRACE, DEBUG, INFO, WARN, ERROR), search, and app filtering.

**Traces** - Span data with duration color-coding (green < 10ms, yellow < 100ms, red > 100ms).

**Metrics** - Counter and gauge values grouped by category, with per-app filtering.

All data streams via SSE from the yeti-telemetry extension.

## Auth

The Auth tab manages users and roles when yeti-auth is enabled:

**Users** - Create, edit, and delete users. Assign roles. View active/inactive status.

**Roles** - Define roles with granular permissions (database, table, and attribute level). The `super_user` role is protected from deletion.

## Vectors

The Vectors tab manages embedding models when yeti-vectors is enabled:

**Text Models** / **Image Models** - View available models, install/uninstall from disk, set the default model per type.

## Benchmarks

The Benchmarks tab runs performance tests against the server:

- Select a test and click **Run**
- View throughput (req/s), latency (p50/p99), and coefficient of variation
- Click the history icon to view past runs and trend charts

## Login

Studio requires authentication when yeti-auth is configured. Sign in with username/password or OAuth (if configured). In development mode without auth, Studio is accessible without login.

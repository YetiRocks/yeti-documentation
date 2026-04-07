<p align="center">
  <img src="https://cdn.prod.website-files.com/68e09cef90d613c94c3671c0/697e805a9246c7e090054706_logo_horizontal_grey.png" alt="Yeti" width="200" />
</p>

---

# yeti-documentation

[![Yeti](https://img.shields.io/badge/Yeti-Application-blue)](https://yetirocks.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![mdBook](https://img.shields.io/badge/mdBook-Powered-orange)](https://rust-lang.github.io/mdBook/)

> **[Yeti](https://yetirocks.com)** - The Performance Platform for Agent-Driven Development.
> Schema-driven APIs, real-time streaming, and vector search. From prompt to production.

**The official documentation site for the Yeti platform.** Comprehensive, searchable, self-hosted.

yeti-documentation serves the complete Yeti platform reference as a static site built with mdBook. Over 80 pages covering installation, core concepts, guides, SDK reference, API documentation, architecture, deployment, and examples -- all compiled to fast static HTML and served directly through Yeti's static file hosting. No external documentation service. No build server. One application, zero runtime dependencies.

---

## Why yeti-documentation

Platform documentation should live where the platform lives. External hosted docs go stale, require separate deployments, and break when the network is down. Self-hosted docs that ship with the platform stay accurate, deploy atomically, and work offline.

yeti-documentation solves this by being a standard Yeti application:

- **Ships with the platform** -- documentation is always available at the same host as the APIs it describes. No separate docs site to maintain or deploy.
- **mdBook-powered** -- Markdown source compiles to fast, searchable static HTML with syntax highlighting, a collapsible sidebar, and print support. Writers focus on content, not tooling.
- **Full-text search** -- built-in elasticlunr.js search indexes every page at build time. Boolean AND queries, title boosting, and heading-level splits provide precise results without a search server.
- **Custom Yeti theme** -- branded CSS layers over mdBook's standard themes (Rust, Navy, Ayu) with custom highlight styles. Consistent look across light and dark modes.
- **Zero runtime cost** -- no database tables, no custom resources, no plugin compilation. Pure static file serving through Yeti's built-in `static_files` handler with 404 fallback.
- **Offline-capable** -- once loaded, the entire documentation site works without network access. Every page, search index, and asset is served from local files.

---

## Quick Start

### 1. Install

```bash
cd ~/yeti/applications
git clone https://github.com/yetirocks/yeti-documentation.git
```

Restart yeti. No compilation required -- this is a static-files-only application that loads instantly.

### 2. Browse the docs

Open your browser to:

```
https://localhost:9996/documentation/
```

The full documentation site is available immediately, including search.

### 3. Rebuild after edits

If you modify any Markdown source files:

```bash
cd ~/yeti/applications/yeti-documentation/source
mdbook build
```

The built HTML is written to `web/` and served by Yeti on the next request. No restart needed.

---

## Architecture

```
Browser
  |
  +-- GET /documentation/* -----> Yeti (static_files handler)
                                    |
                                    v
                              +---------------------------+
                              |   yeti-documentation      |
                              |                           |
                              |   web/                    |
                              |   +-- index.html          |
                              |   +-- guides/*.html       |
                              |   +-- api/*.html          |
                              |   +-- sdk/*.html          |
                              |   +-- searchindex.json    |
                              |   +-- book.js             |
                              |   +-- 404.html            |
                              +---------------------------+
                                    |
                                    v
                              mdBook (build-time only)
                                    |
                                    v
                              source/
                              +-- SUMMARY.md (table of contents)
                              +-- README.md (landing page)
                              +-- getting-started/*.md
                              +-- concepts/*.md
                              +-- guides/*.md (18 guides)
                              +-- sdk/*.md
                              +-- api/*.md
                              +-- reference/*.md
                              +-- architecture/*.md
                              +-- deployment/*.md
                              +-- theme/ (custom CSS + Handlebars)
```

**Request path:** Browser request -> Yeti router -> `static_files` handler -> serves pre-built HTML from `web/` directory -> 404.html fallback for unknown paths.

**Build path:** Edit Markdown in `source/` -> `mdbook build` -> compiled HTML, CSS, JS, and search index written to `web/` -> Yeti serves updated files immediately.

---

## Features

### Documentation Coverage

The site covers the entire Yeti platform across 80+ pages organized into 10 sections:

| Section | Pages | Topics |
|---------|-------|--------|
| **Getting Started** | 3 | Installation, quickstart, first application |
| **Core Concepts** | 5 | Applications, schemas, resources, extensions, routing |
| **Guides** | 37 | CRUD, FIQL, auth (6 guides), real-time (4 guides), extensions (3 guides), caching (3 guides), vector search, GraphQL, gRPC, MCP, telemetry, troubleshooting |
| **SDK Reference** | 8 | Resource macros, request parsing, response helpers, table access, ResourceParams, utilities, extension API |
| **Configuration** | 6 | Server config, app config, schema directives, environment variables, CLI arguments, TLS |
| **API Reference** | 5 | REST, GraphQL, MCP, error codes, data types |
| **Architecture** | 6 | System overview, storage engine, plugin system, telemetry pipeline, security, replication |
| **Deployment** | 5 | Production checklist, performance tuning, monitoring, backup, Yeti Cloud |
| **Examples** | 1 | Overview of example applications |
| **Appendix** | 3 | API compatibility matrix, benchmarks, migration guide |

### Full-Text Search

mdBook's built-in search is configured for precision:

- **Boolean AND** -- all search terms must match (not just any one)
- **Title boost 2x** -- page titles rank higher than body text
- **Heading splits** -- headings down to H3 are individually indexed
- **30-word teasers** -- search results show context around the match
- **30-result limit** -- prevents overwhelming result lists
- **Term expansion** -- partial word matches are included

### Custom Theme

Three custom CSS files layer over mdBook's standard themes:

| File | Purpose |
|------|---------|
| `theme/yeti.css` | Yeti brand colors, typography, sidebar styling |
| `theme/custom.css` | Layout overrides, code block styling, table formatting |
| `theme/index.hbs` | Custom Handlebars template for page structure |

Syntax highlighting uses four theme files: `highlight.css`, `ayu-highlight.css`, `tomorrow-night.css`, and mdBook's built-in Rust theme.

### Static File Serving

Yeti's `static_files` configuration handles all serving:

- Files served from the `web/` directory
- Custom 404 page (`404.html`) for unknown routes
- All standard HTTP caching headers
- No plugin compilation, no database, no runtime overhead

### Print Support

mdBook's print output is enabled -- all 80+ pages can be rendered as a single printable document at `/documentation/print.html`.

---

## Configuration

### config.yaml

```yaml
# Application metadata
name: "Documentation"
app_id: "yeti-documentation"
customer_id: "yeti"
route_prefix: "/documentation"
version: "1.0.0"
description: "Yeti's documentation, powered by mdBook"

static:
  path: web
  route: /
  notFound: 404.html
```

| Field | Value | Description |
|-------|-------|-------------|
| `name` | Documentation | Display name |
| `app_id` | yeti-documentation | Unique application identifier |
| `customer_id` | yeti | Owner namespace |
| `route_prefix` | /documentation | URL path prefix for all routes |
| `version` | 1.0.0 | Application version |
| `static_files.path` | web | Directory containing built HTML |
| `static_files.notFound` | 404.html | Custom 404 error page |

This application has no `schemas:`, `resources:`, `auth:`, or `extensions:` configuration. It is a pure static file server.

### book.toml

mdBook build configuration lives at `source/book.toml`:

```toml
[book]
title = "Yeti Documentation"
description = "Distributed application platform built in Rust"
authors = ["Yeti Team"]
language = "en"
src = "."

[build]
build-dir = "../web"
create-missing = false

[output.html]
default-theme = "rust"
preferred-dark-theme = "navy"
site-url = "/documentation/"
additional-css = ["theme/yeti.css", "theme/custom.css"]
theme = "theme"
```

| Setting | Value | Description |
|---------|-------|-------------|
| `build-dir` | ../web | Output to the `web/` directory Yeti serves |
| `create-missing` | false | Do not auto-create missing pages listed in SUMMARY.md |
| `default-theme` | rust | Light theme on first visit |
| `preferred-dark-theme` | navy | Dark theme for dark-mode users |
| `site-url` | /documentation/ | Base URL for all links (matches route_prefix) |
| `additional-css` | yeti.css, custom.css | Custom theme layers |

---

## Project Structure

```
yeti-documentation/
├── config.yaml                        # Yeti application configuration
├── README.md                          # This file
├── .gitignore                         # Build artifacts exclusions
├── source/                            # mdBook source (Markdown + config)
│   ├── book.toml                      # mdBook build configuration
│   ├── SUMMARY.md                     # Table of contents (defines sidebar)
│   ├── README.md                      # Landing page (Introduction)
│   ├── favicon.png                    # Browser tab icon
│   ├── logo_white.svg                 # Yeti logo for theme
│   ├── theme/                         # Custom theme files
│   │   ├── index.hbs                  # Handlebars page template
│   │   ├── yeti.css                   # Yeti brand styles
│   │   ├── custom.css                 # Layout overrides
│   │   ├── highlight.css              # Light syntax highlighting
│   │   ├── ayu-highlight.css          # Ayu theme highlighting
│   │   └── tomorrow-night.css         # Dark syntax highlighting
│   ├── getting-started/               # Installation and first steps
│   │   ├── installation.md
│   │   ├── quickstart.md
│   │   └── first-application.md
│   ├── concepts/                      # Core platform concepts
│   │   ├── applications.md
│   │   ├── schemas.md
│   │   ├── resources.md
│   │   ├── extensions.md
│   │   └── routing.md
│   ├── guides/                        # How-to guides (37 files)
│   │   ├── studio.md                  # Yeti Studio UI
│   │   ├── defining-schemas.md        # Schema authoring
│   │   ├── custom-resources.md        # Rust resource plugins
│   │   ├── crud.md                    # CRUD operations
│   │   ├── fiql.md                    # FIQL query syntax
│   │   ├── pagination.md             # Pagination and sorting
│   │   ├── field-selection.md         # Sparse fieldsets
│   │   ├── relationships.md           # Table joins
│   │   ├── graphql.md                 # GraphQL usage
│   │   ├── vector-search.md           # Vector/semantic search
│   │   ├── auth-overview.md           # Auth introduction
│   │   ├── auth-mtls.md               # Mutual TLS
│   │   ├── auth-basic.md              # Basic auth
│   │   ├── auth-jwt.md                # JWT tokens
│   │   ├── auth-oauth.md              # OAuth integration
│   │   ├── auth-rbac.md               # Role-based access control
│   │   ├── auth-attributes.md         # Attribute-level permissions
│   │   ├── auth-hooks.md              # Auth hook extensions
│   │   ├── realtime-overview.md       # Real-time features intro
│   │   ├── sse.md                     # Server-Sent Events
│   │   ├── websocket.md               # WebSocket subscriptions
│   │   ├── pubsub.md                  # PubSub patterns
│   │   ├── mqtt.md                    # MQTT broker
│   │   ├── building-extensions.md     # Extension development
│   │   ├── extension-lifecycle.md     # Extension hooks
│   │   ├── event-subscribers.md       # Event subscriber pattern
│   │   ├── caching.md                 # Caching strategies
│   │   ├── full-page-cache.md         # Full-page cache
│   │   ├── table-expiration.md        # TTL-based expiration
│   │   ├── rate-limiting.md           # Rate limiting
│   │   ├── redirects.md               # URL redirects
│   │   ├── telemetry.md               # Observability
│   │   ├── grpc.md                    # gRPC endpoints
│   │   ├── mcp.md                     # Model Context Protocol
│   │   ├── seed-data.md               # Data loading
│   │   ├── static-files.md            # Static file serving
│   │   └── troubleshooting.md         # Common issues
│   ├── sdk/                           # SDK reference (8 files)
│   │   ├── overview.md
│   │   ├── resource-macros.md
│   │   ├── request-parsing.md
│   │   ├── response-helpers.md
│   │   ├── table-access.md
│   │   ├── resource-params.md
│   │   ├── utilities.md
│   │   └── extension-api.md
│   ├── api/                           # API reference (5 files)
│   │   ├── rest.md
│   │   ├── graphql.md
│   │   ├── operations.md
│   │   ├── errors.md
│   │   └── data-types.md
│   ├── reference/                     # Configuration reference (6 files)
│   │   ├── server-config.md
│   │   ├── app-config.md
│   │   ├── schema-directives.md
│   │   ├── environment-variables.md
│   │   ├── cli.md
│   │   └── tls.md
│   ├── architecture/                  # Architecture docs (6 files)
│   │   ├── overview.md
│   │   ├── storage.md
│   │   ├── plugins.md
│   │   ├── telemetry.md
│   │   ├── security.md
│   │   └── replication.md
│   ├── deployment/                    # Deployment guides (5 files)
│   │   ├── production.md
│   │   ├── performance.md
│   │   ├── monitoring.md
│   │   ├── backup.md
│   │   └── cloud.md
│   ├── examples/                      # Example applications
│   │   └── overview.md
│   ├── contributing/                  # Contributor docs
│   │   └── architecture-decisions.md
│   └── appendix/                      # Supplementary material
│       ├── api-compatibility.md
│       ├── benchmarks.md
│       └── migration.md
└── web/                               # Built output (served by Yeti)
    ├── index.html                     # Landing page
    ├── 404.html                       # Custom error page
    ├── searchindex.json               # Full-text search index
    ├── book.js                        # mdBook runtime
    ├── print.html                     # Single-page print view
    ├── getting-started/               # Compiled HTML sections
    ├── concepts/
    ├── guides/
    ├── sdk/
    ├── api/
    ├── reference/
    ├── architecture/
    ├── deployment/
    ├── examples/
    ├── contributing/
    ├── appendix/
    ├── css/                           # Compiled stylesheets
    ├── fonts/                         # Web fonts
    └── FontAwesome/                   # Icon library
```

---

## Development Workflow

### Prerequisites

Install mdBook:

```bash
cargo install mdbook
```

### Edit and preview

```bash
cd ~/yeti/applications/yeti-documentation/source

# Live preview with auto-rebuild on save
mdbook serve

# Opens at http://localhost:3000
# Changes rebuild automatically when files are saved
```

### Build for production

```bash
cd ~/yeti/applications/yeti-documentation/source
mdbook build

# Output written to ../web/
# Yeti serves the new files on next request
```

### Add a new page

1. Create the Markdown file in the appropriate directory:

```bash
echo "# New Topic\n\nContent here." > source/guides/new-topic.md
```

2. Add an entry to `source/SUMMARY.md` in the correct section:

```markdown
- [New Topic](guides/new-topic.md)
```

3. Rebuild:

```bash
cd source && mdbook build
```

The `create-missing = false` setting in `book.toml` means mdBook will error if SUMMARY.md references a file that does not exist, catching broken links at build time.

### Content organization

| Directory | Content type | When to use |
|-----------|-------------|-------------|
| `getting-started/` | Installation and onboarding | New user first steps |
| `concepts/` | Explanations of core ideas | "What is X and why does it exist" |
| `guides/` | Step-by-step how-to articles | "How do I accomplish Y" |
| `sdk/` | SDK API documentation | Rust types, macros, and functions |
| `api/` | Protocol-level API docs | REST, GraphQL, MCP endpoints |
| `reference/` | Configuration reference | Config files, env vars, CLI flags |
| `architecture/` | System internals | Storage, plugins, security, replication |
| `deployment/` | Operations guides | Production, monitoring, backup |
| `examples/` | Example applications | Working apps with source code |
| `appendix/` | Supplementary material | Compatibility, benchmarks, migration |

### Writing conventions

- Use `#` for the page title (one per file)
- Use `##` and `###` for sections (indexed by search up to H3)
- Wrap code examples in fenced blocks with language tags for syntax highlighting
- Use relative links between pages (e.g., `../guides/crud.md`)
- Add new pages to SUMMARY.md before building -- `create-missing = false` enforces this

---

## Comparison

| | yeti-documentation | External Docs Hosting |
|---|---|---|
| **Deployment** | Ships with the platform, same host | Separate service, separate deploy pipeline |
| **Availability** | Works offline, no network required | Requires internet access |
| **Search** | Built-in client-side search, no server | Typically requires search service (Algolia, etc.) |
| **Build** | `mdbook build` -- single command, seconds | CI/CD pipeline, build minutes, deploy steps |
| **Versioning** | Git-tracked Markdown alongside the platform | Often decoupled from platform releases |
| **Runtime** | Zero -- static files only | Web server, CDN, search backend |
| **Customization** | CSS + Handlebars templates | Platform-dependent, often limited |
| **Cost** | Free | Hosting fees, search API costs |

---

Built with [Yeti](https://yetirocks.com) | The Performance Platform for Agent-Driven Development

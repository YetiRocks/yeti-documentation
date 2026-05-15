# Crate Layout

Yeti's `crates/` tree mirrors the journey a request takes through the
system. Reading the directory should answer **"what is this code's
role?"** without opening any files.

Canonical source: [`STRUCTURE.md`](https://github.com/yetiRocks/yeti/blob/main/STRUCTURE.md) in the yeti repo.

## The six bands

```
crates/
├── foundation/   vocabulary; zero or near-zero yeti deps
│                 yeti-types · yeti-schema · yeti-store · yeti-objects
│
├── sdk/          customer-facing surface — every app does
│                 `use yeti_sdk::prelude::*`
│                 yeti-sdk · yeti-sdk-macros
│
├── request/      the five-stage request pipeline
│                 yeti-http · yeti-mqtt · yeti-graphql · yeti-mcp
│                 yeti-router · yeti-auth · yeti-ratelimit · yeti-table
│
├── plugins/      statically-compiled cross-cutting services
│                 yeti-ai · yeti-admin · yeti-alerts · yeti-audit
│                 yeti-telemetry · yeti-data-loader · yeti-installer
│                 yeti-workspace · yeti-compiler
│
├── fabric/       cluster + cloud control plane
│                 yeti-control · yeti-build · yeti-cluster
│
└── runtime/      the long-running process(es)
                  yeti-host · yeti-host-testing
                  yeti-server · yeti-jobs · yeti-jobs-testing
                  yeti-cli  (the `yeti` binary lives here)
```

## The five-stage request flow

```
Stage 1  Protocol      → http / mqtt / graphql / mcp arrive
Stage 2  Router        → app_id, resource_id, query_params resolved
Stage 3  Auth + limits → identity, access, permission, quota attached
Stage 4  Table reg     → database, table_name resolved
Stage 5  Dispatch      → handler runs, response produced
```

All eight crates in `request/` participate in this single flow.

## Layer rules

Higher layers may depend on lower layers; the reverse is rejected by the
audit's Phase 8 (`audit/policies/layer-map.toml`).

| Layer | Crates | Role |
|---|---|---|
| L0 | `yeti-types` | Pure vocabulary; zero yeti deps |
| L1 | `yeti-schema`, `yeti-store`, `yeti-objects`, `yeti-sdk-macros` | Early substrates |
| L2 | `yeti-sdk` | **The only customer-facing surface** — everything else is internal |
| L3 | `yeti-table`, `yeti-router`, `yeti-auth`, `yeti-ratelimit` | Request pipeline core |
| L4 | `yeti-http`, `yeti-mqtt`, `yeti-graphql`, `yeti-mcp`, all plugins, all fabric | Protocol + cross-cutting |
| L5 | `yeti-host` | FFI host (cdylib boundary) |
| L6 | `yeti-server`, `yeti-jobs` | Long-running processes |
| L7 | `yeti-cli` | CLI entry |

## The cdylib boundary

Apps compile as `cdylib`, not workspace members. The boundary sits
between `yeti-sdk` (apps see) and `yeti-host` (host owns). See
[Plugins & Hot Reload](plugins.md) for the dylib rules customers need
to respect.

## See also

- [`STRUCTURE.md`](https://github.com/yetiRocks/yeti/blob/main/STRUCTURE.md) — canonical
- [Plugins & Hot Reload](plugins.md) — dylib boundary, compilation, hot reload
- [Plugin API](../sdk/plugin-api.md) — the `Plugin` trait that everything in `plugins/` and `request/yeti-auth`-style services implement

# Service Bridge

Plugin-only reference. The yeti-service-bridge is the cross-FFI plumbing
behind `fetch`, `publish`, `subscribe`, `limiter()`, and `yeti_log` —
one polymorphic Tower `Service<R>` dispatch through the cdylib boundary
instead of N bespoke C-ABI pairs (YTC-281 / YTC-282, May 2026).

App authors **don't need this page**. Use `fetch()`, `publish()`, etc.
from the SDK prelude. This page is for plugin authors adding a brand
new cross-FFI capability.

## The model

```
┌──────────────────────┐                   ┌──────────────────────┐
│  Plugin (dylib)      │                   │  Host (yeti-host)    │
│                      │                   │                      │
│  service.call(req)   │                   │  ServiceRegistry     │
│         │            │                   │   ├─ "publish"  ┐    │
│         ▼            │                   │   ├─ "fetch"    │    │
│  HostServiceHandle ──┼──── one C-ABI ────┼─→ ├─ "log"      │    │
│  ::lookup("name")    │     pair          │   ├─ "ratelimit"│    │
│                      │                   │   └─ "subscribe"┘    │
└──────────────────────┘                   └──────────────────────┘
```

The host registers each capability as a Tower `Service<Bytes>` (unary)
or `StreamingBridge` (streaming). The dylib looks the service up by
name and calls it via the polymorphic `yeti_service_call` extern. The
host-side service is a normal Tower service — `ServiceBuilder` layers,
typed request/response, `tower::Service` impls.

## Registering a host service

Inside `crates/runtime/yeti-host/src/application/service_bridge_init.rs`:

```rust,ignore
use yeti_service_bridge_host::ServiceRegistry;
use tower::service_fn;

let mut reg = ServiceRegistry::new();

// Unary: one request → one response
reg.register_unary("my_thing", service_fn(|req: Bytes| async move {
    let request: MyRequest = decode(&req)?;
    let response = handle(request).await?;
    Ok::<Bytes, BridgeError>(encode(&response))
}));

// Streaming: one request → many response frames
reg.register_streaming("my_stream", MyStreamingBridge { /* ... */ });

reg.install();
```

`install()` publishes the registry to the process-global static so the
FFI `yeti_get_service(name)` extern can look services up.

## Consuming a host service from the SDK

Inside `crates/sdk/yeti-sdk/src/your_module.rs`:

```rust,ignore
use yeti_service_bridge::{HostServiceHandle, call_unary};

static HANDLE: OnceLock<HostServiceHandle> = OnceLock::new();

fn handle() -> Option<&'static HostServiceHandle> {
    HANDLE.get_or_init(|| HostServiceHandle::lookup("my_thing")?).into()
    // …or use the `cached_handle!("my_thing")` macro in yeti-service-bridge
}

pub async fn my_thing(req: MyRequest) -> Result<MyResponse> {
    let svc = handle().ok_or(YetiError::Internal("service not registered"))?;
    let req_bytes = encode(&req);
    let resp_bytes = call_unary(svc, &req_bytes, decode).await?;
    Ok(resp_bytes)
}
```

The lookup is cached in `OnceLock` so subsequent calls skip the
registry hash. `call_unary` returns a future that polls the host task
through the FFI waker plumbing — no thread hops on the dylib side.

## Why polymorphic Tower, not bespoke C-ABI pairs

Before YTC-281, each capability had its own `extern "C"` pair:

| Bridge | SDK side | Host side | Total |
|---|---:|---:|---:|
| http_bridge | 168 | 494 | 662 |
| subscribe_bridge | 273 | 196 | 469 |
| publish_bridge | 142 | 180 | 322 |
| ratelimit_bridge | 195 | 109 | 304 |
| log_bridge | 149 | — | 149 |

~2.7k LOC of hand-rolled marshaling. The Tower service-bridge model
collapses this to **one** C-ABI pair (`yeti_get_service` +
`yeti_service_call` + waker poll/drop) plus a typed wrapper per
service. Each new capability adds ~30 LOC SDK-side and ~40 LOC
host-side instead of ~300 LOC.

Day-2 microbench: noop service-bridge call across the cdylib boundary
is **78.9 ns** (vs. 82 ns in-process baseline on the same hardware).
Day-3 publish head-to-head: 1.35× the bespoke-extern path — within
the "ship" envelope per the YTC-282 decision-gate matrix.

## When to use it

| Need | Path |
|---|---|
| Outbound HTTP from a dylib | `fetch()` — already on the bridge |
| Pub/sub publish | `publish()` — already on the bridge |
| Pub/sub subscribe | `subscribe()` — already on the bridge |
| Rate-limit check | `limiter()` — already on the bridge |
| Structured logging | `yeti_log!` — already on the bridge |
| New capability needing host execution (e.g. embeddings, vector queries, secret-manager access, mail send) | **Add a new bridge service** |
| Pure dylib-local compute (no host state, no I/O) | Just write a normal fn — no bridge needed |

The bridge cost is dispatch + marshaling. For hot paths, prefer
keeping work dylib-local; bridge only when the host owns the resource
(a connection pool, a singleton, a privilege).

## Day-3.5 dispatch-core optimization

The FFI shim (`crates/runtime/yeti-host/src/service_bridge/ffi.rs`) is
allocation-tight:

- **Sync fast path**: if the first poll of the host future resolves
  inline, the task state stashes the response `Bytes` directly and
  drops the future. Common case (publish, ratelimit, log) — 1 alloc
  per call.
- **Async path**: future stored in `Box<TaskState::Pending>` for
  re-polling. 2 allocs per call (state + box).
- **`TaskHandle` is `repr(transparent)`** over `*mut TaskState` — no
  wrapper box.
- **`Waker::noop()`** for the inline first poll (no clone needed).

## See also

- `yeti-service-bridge` crate docs (foundation/) — full FFI surface
- ADR-006 (in repo) — the polymorphic-service-bridge architectural decision
- [Plugin API](plugin-api.md) — where most plugin authors should start
- [Crate Layout](../architecture/crate-layout.md) — the L0–L7 layering

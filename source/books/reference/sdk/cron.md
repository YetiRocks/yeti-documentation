# Scheduled Functions — `#[schedule]`

Declarative cron-style fn registration. Tag a free function with
`#[schedule(every = "...")]` and yeti will invoke it on the interval.

```rust,ignore
use yeti_sdk::prelude::*;

#[schedule(every = "5m")]
async fn refresh_cache(ctx: &Context) -> Result<()> {
    let table = ctx.table("Cache")?;
    table.delete_all().await?;
    yeti_log::info!("Cache cleared");
    Ok(())
}
```

That's the whole API. The macro:

1. Validates the signature (must take exactly `&Context`, no methods).
2. Computes a stable hash of the function shape (catches drift if
   yeti changes the expected signature).
3. Emits a hidden module that registers the fn into a static inventory.
4. The host scans the inventory at app load and schedules the fn on
   its tokio runtime.

## Interval format

```rust,ignore
#[schedule(every = "30s")]    // 30 seconds
#[schedule(every = "5m")]     // 5 minutes
#[schedule(every = "1h")]     // 1 hour
#[schedule(every = "24h")]    // daily-ish
```

Parsed via [`humantime`](https://docs.rs/humantime). Sub-second
intervals are accepted but not recommended.

`cron = "..."` is reserved for cron-expression support and accepted at
parse time, but the runtime currently only honors `every = "..."`.
Mixing both is a compile error.

## Signature rules

- Function must be `pub` or visible from the crate root.
- Single argument: `&Context`. No other params (no caller to provide them).
- Return type is your choice — `()`, `Result<()>`, or anything `Display`-able.
  Errors are logged; they don't halt the schedule.
- Functions can be `async` or sync. Async runs on the host tokio runtime.

```rust,ignore
// Sync — fine for short, CPU-bound work
#[schedule(every = "1m")]
fn rotate_metrics(ctx: &Context) {
    yeti_log::debug!("[{}] metrics tick", ctx.app_id);
}

// Async — required for I/O or table access
#[schedule(every = "10m")]
async fn purge_expired(ctx: &Context) -> Result<()> {
    let now = unix_timestamp()?;
    let cutoff = json!(now - 86_400);
    let stale = ctx.table("Session")?
        .query()
        .where_lt("createdAt", cutoff)
        .execute()
        .await?;
    for s in stale {
        if let Some(id) = s["id"].as_str() {
            ctx.table("Session")?.delete(id).await?;
        }
    }
    Ok(())
}
```

## What `&Context` gives you

The scheduled-fn `Context` is request-less — no `method`, no `body`,
no `headers`. It carries the populated runtime fields:

- `ctx.app_id` — your app's id
- `ctx.backend_manager` — backend access for table ops
- `ctx.root_directory` — filesystem root
- `ctx.table(name)?` / `ctx.tables()?` — same as in request handlers

This is the same `Context` that `Plugin::on_ready()` receives.

## Errors

A scheduled fn that returns `Err` or panics is logged but does **not**
get unscheduled. The next tick fires normally.

```rust,ignore
#[schedule(every = "1m")]
async fn ping_upstream(ctx: &Context) -> Result<()> {
    let resp = fetch("https://status.example.com/healthz").send()?;
    if !resp.ok() {
        return Err(YetiError::Internal(format!("upstream {}", resp.status)));
    }
    Ok(())
}
```

A persistent error pattern shows up in the telemetry log; fix it
there.

## Caveats

- **Drift**: scheduled fns don't carry per-run state. If you need
  "run only when X has changed," store the last-run timestamp in a
  table.
- **Overlap**: if a tick is still running when the next interval
  arrives, the next tick runs anyway. Use a mutex or table-level
  CAS (`put_if`) for serialization.
- **Cluster mode**: every node runs its own copy of `#[schedule]`
  fns. For "exactly once across the cluster" semantics, use a
  leader-lease primitive or coordinate via a CAS write to a
  designated table.

## See also

- [Plugin API](plugin-api.md) — `on_ready()` for one-shot startup work
- [Table Access](table-access.md) — `put_if` for CAS coordination
- [Utilities](utilities.md) — `fetch`, `yeti_log`, `unix_timestamp`

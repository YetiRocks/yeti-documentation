# Utilities

Everything here is in `yeti_sdk::prelude::*`.

## HTTP — `fetch(url)`

Dylib-safe outbound HTTP. The bridge routes through the host's
`yeti-http-client` (rama-backed); calling `reqwest` directly from a
dylib crashes the host runtime.

```rust,ignore
// GET → JSON
let data: Value = fetch("https://api.example.com/data").json()?;

// POST with JSON body
let user: User = fetch("https://api.example.com/users")
    .method("POST")
    .header("Authorization", &format!("Bearer {token}"))
    .json_body(&json!({"name": "Alice"}))?
    .json()?;

// Form body
fetch("https://oauth.example.com/token")
    .method("POST")
    .header("Content-Type", "application/x-www-form-urlencoded")
    .body("grant_type=authorization_code&code=abc")
    .send()?;

// Raw response inspection
let resp = fetch("https://api.example.com/data").send()?;
if resp.ok() { /* ... */ }

// No redirects + custom timeout
fetch("https://slow.example.com")
    .no_redirect()
    .timeout(5)
    .send()?;
```

Per-method constructors are also available:

```rust,ignore
FetchBuilder::post(url).json_body(&body)?.json()?
FetchBuilder::put(url).header("k", "v").send()?
FetchBuilder::delete(url).send()?
```

### FetchBuilder

| Method | Effect |
|---|---|
| `header(k, v)` | Add a request header |
| `body(s)` | Set raw body (string or bytes) |
| `json_body(&v)` | Set body + `Content-Type: application/json` |
| `method(verb)` | Override method (for dynamic verbs) |
| `no_redirect()` | Disable redirect following |
| `timeout(secs)` | Per-request timeout (default 30s) |
| `.json::<T>()` | Send, ensure 2xx, deserialize |
| `.text()` | Send, ensure 2xx, return body string |
| `.send()` | Send, return raw `FetchResponse` |

### FetchResponse

```rust,ignore
pub struct FetchResponse {
    pub status: u16,
    pub body: Vec<u8>,
    pub headers: HashMap<String, String>,
    pub url: String,
    pub redirected: bool,
}

impl FetchResponse {
    fn ok(&self) -> bool                   // 200–299
    fn ensure_ok(self) -> Result<Self>     // self if 2xx else error
    fn json<T>(&self) -> Result<T>         // deserialize body
    fn text(&self) -> Result<&str>         // UTF-8 body
    fn bytes(&self) -> &[u8]
    fn header(&self, name: &str) -> Option<&str>  // case-insensitive
}
```

## Pub/Sub — `publish()` / `subscribe()`

Dylib-safe table notifications. Routes through the service-bridge.

```rust,ignore
// Publish an update — receivers get the value
publish("Sensor", "temp-3", Some(&json!({"celsius": 21.4})));

// Publish a delete — receivers see op=delete
publish("Sensor", "temp-3", None);

// Subscribe to all row changes on a table
let _sub = subscribe("Sensor", |msg| {
    yeti_log::info!("Sensor {:?} updated: {:?}", msg.id, msg.data);
})?;
```

`subscribe()` runs `handler` on a dedicated OS thread per subscription
(keep handlers short — hand off to worker pools if you need parallelism).
The returned `Subscription` keeps the thread alive; drop it to stop.
Returns `None` when the bridge isn't reachable (e.g. unit tests without
yeti-host).

## Rate limiting — `limiter()`

```rust,ignore
use yeti_sdk::ratelimit::limiter;

let lim = limiter()?;
match lim.check(scope, key).await {
    Ok(()) => { /* token consumed */ },
    Err(retry_after) => return Err(retry_after.to_yeti_error()),
}
```

The default `limiter()` returns a host-backed `RateLimiter` that routes
every `check()` through the service-bridge `"ratelimit"` service.
`scope` is typically the resource name; `key` is per-tenant or
per-identity. Transport failures fail **open** (treated as `Ok`).

## Logging

Use the standard `log` crate. yeti-sdk installs a global logger that
routes records through the service-bridge `"log"` service so they
reach the host subscriber. **`tracing::*` from a dylib doesn't reach
the host** because of TLS isolation — use `log` instead.

```rust,ignore
use log::{info, warn, error, debug, trace};

info!("Processing {} items", items.len());
warn!("Cache miss for key={}", key);
error!("Failed to import: {}", err);
```

## Cookies

### Build a `Set-Cookie`

Defaults: `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`.

```rust,ignore
let cookie = CookieBuilder::new("session_id", &token)
    .max_age(3600)
    .same_site(SameSite::Lax)
    .build();

reply()
    .header("set-cookie", &cookie)
    .json(json!({"ok": true}))

// Delete
reply().header("set-cookie", &CookieBuilder::delete("session_id"))
```

### Parse cookies from requests

```rust,ignore
let session = CookieParser::get_cookie(&request, "session_id");

// Tries cookie first, then X-Session-Id header
let session = CookieParser::get_session_id(&request, "yeti_session");

let all = CookieParser::parse_all(&request);
```

`CookieParser::parse_all` handles HTTP/2 split `Cookie` headers (RFC 7540 §8.1.2.5).

## IDs

```rust,ignore
let id = generate_id();
// "018e7a9f-3c4d-7890-abcd-ef1234567890"  — UUID v7, time-sortable
```

UUID v7 strings; sortable by creation time for B-tree locality and
chronological scans.

## Tokens

```rust,ignore
TokenGenerator::generate(32)   // 64 hex chars (32 random bytes)
TokenGenerator::csrf_token()    // 64 hex chars (alias for generate(32))
```

## Timestamps

```rust,ignore
unix_timestamp()?    // u64 seconds since epoch (fallible — needs ?)
now_secs()           // u64 seconds since epoch (infallible)
now_ms()             // u64 milliseconds since epoch
delay(ms).await      // async sleep
```

## Composite keys

```rust,ignore
let key = composite_key(&["user-123", "2026-05-15", "metrics"]);
// "user-123::2026-05-15::metrics"
```

## CSV → JSON

```rust,ignore
let items: Vec<Value> = parse_csv(&ctx.body);
```

```csv
name,price,category        →    [{"name":"Widget","price":"29.99","category":"Tools"},
Widget,29.99,Tools              {"name":"Gadget","price":"49.99","category":"Electronics"}]
Gadget,49.99,Electronics
```

## Bulk upsert

Validate + key-extract + upsert in one pass. Returns counts and per-row errors.

```rust,ignore
resource!(Import {
    post(ctx) => {
        let table = ctx.table("Product")?;
        let body = ctx.require_json_body()?;
        let items = body.as_array().cloned().unwrap_or_else(|| parse_csv(&ctx.body));

        let result = bulk_upsert(&table, items,
            |item| item["id"].as_str().map(str::to_owned),
            |item| {
                item["name"].as_str().ok_or("missing name")?;
                Ok(item.clone())
            },
        ).await?;

        reply().json(result.to_json("Imported"))
        // {"message":"Imported","created":45,"updated":3,"errors":[...]}
    }
});
```

## Validation

```rust,ignore
validate_identifier("my-resource-id", "resourceId")?;
// Err(YetiError::Validation) if invalid characters
```

## Quick reference

| Fn | Returns | Description |
|---|---|---|
| `fetch(url)` | `FetchBuilder` | Dylib-safe HTTP via service-bridge |
| `publish(table, id, value)` | `Confirmation` | Pub/Sub publish |
| `subscribe(table, handler)` | `Option<Subscription>` | Pub/Sub subscribe |
| `limiter()` | `Result<Arc<dyn RateLimiter>>` | Acquire rate limiter |
| `generate_id()` | `String` | UUID v7 |
| `unix_timestamp()` / `now_secs()` / `now_ms()` | numeric | Current time |
| `delay(ms).await` | `()` | Async sleep |
| `composite_key(&[...])` | `String` | Join with `::` |
| `parse_csv(bytes)` | `Vec<Value>` | CSV → JSON objects |
| `bulk_upsert(...)` | `Result<BulkResult>` | Batch upsert with validation |
| `validate_identifier(id, field)` | `Result<()>` | Identifier format check |
| `TokenGenerator::generate(len)` | `String` | Random hex |
| `CookieBuilder::new(name, value)` | `CookieBuilder` | Build Set-Cookie |
| `CookieParser::get_cookie(req, name)` | `Option<String>` | Read a cookie |

See [Service Bridge](service-bridge.md) for the dylib→host plumbing
behind `fetch`, `publish`, `subscribe`, `limiter`, and `log`.

# Response Helpers

Three layers — free functions for the common case, `reply()` builder
for headers and custom content types, and a few specialized helpers
for futures and `YetiError` conversion. All errors are
**RFC 9457 Problem Details** by default.

```rust,ignore
resource!(Item {
    get(ctx) => ok(ctx.table("Item")?.get_or_404(ctx.require_id()?).await?),
    post(ctx) => created(ctx.table("Item")?.create(ctx.require_json_body()?.clone()).await?),
    delete(ctx) => { ctx.table("Item")?.delete(ctx.require_id()?).await?; no_content() },
});
```

## Free functions

### Success

| Fn | Effect |
|---|---|
| `ok(data)` | 200 + JSON |
| `created(data)` | 201 + JSON |
| `created_with_location(id)` | 201 + `Location` header |
| `no_content()` | 204 empty body |
| `ok_json_bytes(bytes)` | 200 + pre-serialized JSON (skips serde) |
| `ok_html(html)` | 200 + `text/html` |
| `ok_text(text)` | 200 + `text/plain` |
| `ok_with_content_type(mime, data)` | 200 + custom MIME |

### Errors — RFC 9457

```json
{
  "type": "urn:yeti:error:404",
  "title": "Not Found",
  "status": 404,
  "detail": "Record not found: user-123"
}
```

| Fn | Effect |
|---|---|
| `bad_request(msg)` | 400 problem+json |
| `not_found(msg)` | 404 problem+json |
| `unauthorized(msg)` | 401 problem+json |
| `internal_error(msg)` | 500 problem+json |
| `error_response(status, msg)` | Custom status, problem+json |
| `structured_error_response(&err)` | Convert any `YetiError` → its Problem Details |
| `html_response(status, html)` | Custom status + HTML |
| `text_response(status, text)` | Custom status + plain text |

```rust,ignore
bad_request("Invalid email format")          // 400
not_found("User not found")                  // 404
error_response(422, "Validation failed")     // 422

// Convert any YetiError automatically
let err = YetiError::NotFound { resource_type: "User".into(), id: "123".into() };
structured_error_response(&err)              // 404 with the structured Problem
```

### Domain-specific helpers

Less boilerplate for common error patterns:

| Fn | Effect |
|---|---|
| `storage_error(err)` | 500: "Storage error: {err}" |
| `serialization_error(err)` | 500: "Serialization error: {err}" |
| `invalid_json(err)` | 400: "Invalid JSON: {err}" |
| `record_not_found(key)` | 404: "Record not found: {key}" |
| `missing_param(param)` | 400: "Missing '{param}' parameter" |

### `get_or_not_found(...)`

Eliminate the `match`-on-`Option` boilerplate for raw backend lookups:

```rust,ignore
let data = match get_or_not_found(backend.get(key).await, &id) {
    Ok(data) => data,
    Err(response) => return Ok(*response),
};
```

Returns the raw bytes on `Ok(Some(...))`, a 404 on `Ok(None)`, a 500
on `Err(...)`.

### Future helpers

For default trait impls and async early returns:

| Fn | Effect |
|---|---|
| `method_not_allowed_future()` | 405 wrapped in `ResourceFuture` |
| `not_implemented_future("subscribe")` | 501 wrapped in `ResourceFuture` |
| `error_future(status, msg)` | Async early-return error |
| `ready(result)` | Wrap a sync `Result` as a future |

## `reply()` — custom status, headers, content types

```rust,ignore
reply().json(data)                                  // 200 + JSON
reply().code(201).json(data)                        // 201 + JSON
reply().code(201).header("x-id", &id).json(data)    // 201 + custom header
reply().html(content)                                // 200 + text/html
reply().csv(csv_string)                              // 200 + text/csv
reply().messagepack(&data)                           // 200 + application/msgpack
reply().cbor(&data)                                  // 200 + application/cbor
reply().redirect("/new-location", Some(302))         // 302 (None → default 302)
reply().code(204).send(Vec::new())                   // 204 no body
reply().type_header("application/xml").send(xml)     // custom content type
```

Builder methods:

| Method | Effect |
|---|---|
| `.code(s)` / `.status(s)` | Status code |
| `.header(k, v)` | Add a header (repeatable — multiple `set-cookie` etc.) |
| `.headers(map)` | Add several at once |
| `.type_header(ct)` | Set `Content-Type` |

Terminal methods consume the builder and return `Result<Response>`:
`.json(v)`, `.html(s)`, `.text(s)`, `.csv(s)`, `.messagepack(v)`,
`.cbor(v)`, `.redirect(url, code)`, `.send(bytes)`.

### Multi-cookie example

```rust,ignore
reply()
    .header("set-cookie", "a=1; Path=/")
    .header("set-cookie", "b=2; Path=/")
    .json(json!({"ok": true}))
```

## `ResponseExt::add_header`

Attach a header to any existing response or result:

```rust,ignore
ok(data).add_header("x-request-id", &id)
ok_html(html).add_header("x-cache", "HIT")
```

Works on `Response<ResponseBody>` and `Result<Response<ResponseBody>>`.

## Decision table

| Need | Use |
|---|---|
| JSON 200 | `ok(data)` |
| JSON 201 | `created(data)` |
| Empty 204 | `no_content()` |
| Pre-serialized JSON | `ok_json_bytes(bytes)` |
| Error with message | `bad_request(msg)`, `not_found(msg)`, `unauthorized(msg)` |
| Error custom status | `error_response(422, msg)` |
| Error from `YetiError` | `structured_error_response(&err)` |
| Custom status + headers | `reply().code(201).header(...).json(data)` |
| HTML / text | `ok_html(s)` or `ok_text(s)` |
| Redirect | `reply().redirect(url, Some(302))` |
| MessagePack / CBOR | `reply().messagepack(v)` / `.cbor(v)` |
| CSV download | `reply().csv(s)` |
| Custom MIME | `ok_with_content_type(mime, bytes)` |
| Add a header to anything | `.add_header(k, v)` |
| Async early return | `error_future(400, "msg")` |

## See also

- [Resource Macros](resource-macros.md) — `resource!()` uses these helpers
- [Request Parsing](request-parsing.md) — `Context` accessors

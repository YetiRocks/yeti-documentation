# Response Helpers

Three layers of response building, from simplest to most flexible. All errors use RFC 9457 Problem Details.

## RFC 9457 Problem Details

Error helpers produce `application/problem+json` responses:

```json
{
  "type": "urn:yeti:error:404",
  "title": "Not Found",
  "status": 404,
  "detail": "Record not found: user-123"
}
```

`ProblemDetails` (from `yeti_types::error`):

| Field | Description |
|-------|-------------|
| `type` | URI reference identifying the problem (e.g. `urn:yeti:error:not_found`) |
| `title` | Short human-readable summary (e.g. "Not Found") |
| `status` | HTTP status code |
| `detail` | Explanation of this occurrence (optional) |

Any `YetiError` converts to `ProblemDetails` via `.to_problem_details()`, mapping variant to status code, type URI, and title.

## Layer 1: Free Functions

Single-call responses. All return `Result<Response<ResponseBody>>`.

### Success responses

```rust,ignore
fn ok<T: Serialize>(data: T) -> Result<Response<ResponseBody>>
fn created<T: Serialize>(data: T) -> Result<Response<ResponseBody>>
fn created_with_location(id: &str) -> Result<Response<ResponseBody>>
fn no_content() -> Result<Response<ResponseBody>>
fn ok_json_bytes(bytes: Vec<u8>) -> Result<Response<ResponseBody>>
```

```rust,ignore
ok(json!({"status": "active"}))              // 200 + JSON
created(json!({"id": "new-123"}))            // 201 + JSON
created_with_location("abc-123")             // 201 + Location header
no_content()                                  // 204 empty
ok_json_bytes(pre_serialized)                 // 200 + pre-serialized JSON (skips serde)
```

### Error responses

```rust,ignore
fn bad_request(message: &str) -> Result<Response<ResponseBody>>
fn not_found(message: &str) -> Result<Response<ResponseBody>>
fn unauthorized(message: &str) -> Result<Response<ResponseBody>>
fn internal_error(message: &str) -> Result<Response<ResponseBody>>
fn error<T: Serialize>(data: T) -> Result<Response<ResponseBody>>
fn error_response(status: u16, message: &str) -> Result<Response<ResponseBody>>
fn structured_error_response(err: &YetiError) -> Result<Response<ResponseBody>>
```

Named helpers delegate to `error_response()`, producing RFC 9457 Problem Details:

```rust,ignore
bad_request("Invalid email format")          // 400 application/problem+json
not_found("User not found")                  // 404 application/problem+json
unauthorized("Token expired")                // 401 application/problem+json
internal_error("Database connection failed") // 500 application/problem+json
error_response(422, "Validation failed")     // custom status, problem+json
```

`error()` is different -- it returns a 400 with a custom JSON body (not Problem Details):

```rust,ignore
error(json!({"field": "email", "msg": "required"}))  // 400 + application/json
```

`structured_error_response()` converts any `YetiError` to its Problem Details representation:

```rust,ignore
let err = YetiError::NotFound { resource_type: "User".into(), id: "123".into() };
structured_error_response(&err)  // 404 application/problem+json
```

### Content-type responses

```rust,ignore
fn ok_html(html: impl AsRef<str>) -> Result<Response<ResponseBody>>
fn ok_text(text: impl AsRef<str>) -> Result<Response<ResponseBody>>
fn ok_with_content_type(content_type: &str, data: impl Into<Vec<u8>>) -> Result<Response<ResponseBody>>
fn html_response(status: u16, html: &str) -> Result<Response<ResponseBody>>
fn text_response(status: u16, text: &str) -> Result<Response<ResponseBody>>
```

```rust,ignore
ok_html("<h1>Hello</h1>")                         // 200 + text/html
ok_text("plain text")                              // 200 + text/plain
ok_with_content_type("image/png", png_bytes)       // 200 + custom MIME
html_response(404, "<h1>Not Found</h1>")           // custom status + HTML
text_response(503, "Service unavailable")          // custom status + text
```

### Domain-specific helpers

Reduce repeated `format!` patterns in handlers:

```rust,ignore
fn storage_error<E: Display>(err: E) -> Result<Response<ResponseBody>>
fn serialization_error<E: Display>(err: E) -> Result<Response<ResponseBody>>
fn invalid_json<E: Display>(err: E) -> Result<Response<ResponseBody>>
fn record_not_found(key: &str) -> Result<Response<ResponseBody>>
fn missing_param(param: &str) -> Result<Response<ResponseBody>>
```

```rust,ignore
storage_error(err)                           // 500: "Storage error: {err}"
serialization_error(err)                     // 500: "Serialization error: {err}"
invalid_json(err)                            // 400: "Invalid JSON: {err}"
record_not_found("user-123")                 // 404: "Record not found: user-123"
missing_param("email")                       // 400: "Missing 'email' parameter"
```

### get_or_not_found pattern

Eliminates match-on-Option boilerplate for raw storage lookups:

```rust,ignore
fn get_or_not_found(
    result: Result<Option<Vec<u8>>>,
    id: &str,
) -> StdResult<Vec<u8>, Box<Response<ResponseBody>>>
```

```rust,ignore
let data = match get_or_not_found(backend.get(key).await, &id) {
    Ok(data) => data,
    Err(response) => return Ok(*response),
};
```

Returns the raw bytes on `Ok(Some(...))`, a 404 Problem Details on `Ok(None)`, or a 500 Problem Details on `Err(...)`.

### Future helpers

For `Resource` trait defaults and early returns in async contexts:

```rust,ignore
fn method_not_allowed_future() -> ResourceFuture
fn not_implemented_future(method_name: &'static str) -> ResourceFuture
fn error_future(status: u16, message: impl Into<String>) -> ResourceFuture
fn ready(result: Result<Response<ResponseBody>>) -> ResourceFuture
```

```rust,ignore
// Default trait implementations
fn put(&self, _req: Request<Vec<u8>>, _params: Params) -> ResourceFuture {
    method_not_allowed_future()                        // 405
}

fn subscribe(&self, _req: Request<Vec<u8>>, _params: Params) -> ResourceFuture {
    not_implemented_future("subscribe")                // 501
}

// Early return from a resource handler
if id.is_empty() {
    return error_future(400, "ID cannot be empty");    // 400
}

// Wrap a synchronous result as a future
return ready(ok(json!({"cached": true})));
```

## Layer 2: Reply Builder

Chain methods for custom status codes, headers, and content types.

```rust,ignore
fn reply() -> ReplyBuilder
```

### ReplyBuilder methods

```rust,ignore
impl ReplyBuilder {
    fn code(self, status: u16) -> Self          // set status code
    fn status(self, status: u16) -> Self        // alias for code()
    fn header(self, key: &str, value: &str) -> Self  // add a header
    fn headers(self, map: HashMap<&str, &str>) -> Self  // add multiple headers
    fn type_header(self, content_type: &str) -> Self    // set Content-Type

    // Terminal methods (consume the builder):
    fn json(self, value: impl Serialize) -> Result<Response<ResponseBody>>
    fn html(self, html: &str) -> Result<Response<ResponseBody>>
    fn text(self, text: &str) -> Result<Response<ResponseBody>>
    fn csv(self, csv_data: impl AsRef<str>) -> Result<Response<ResponseBody>>
    fn messagepack(self, value: impl Serialize) -> Result<Response<ResponseBody>>
    fn cbor(self, value: impl Serialize) -> Result<Response<ResponseBody>>
    fn redirect(self, url: &str, code: Option<u16>) -> Result<Response<ResponseBody>>
    fn send(self, body: Vec<u8>) -> Result<Response<ResponseBody>>
}
```

### Examples

```rust,ignore
reply().json(data)                                // 200 + JSON
reply().code(201).json(data)                      // 201 + JSON
reply().code(201).header("x-id", &id).json(data)  // 201 + custom header + JSON
reply().html(content)                              // 200 + text/html
reply().text(content)                              // 200 + text/plain
reply().csv(csv_string)                            // 200 + text/csv
reply().messagepack(&data)                         // 200 + application/msgpack
reply().cbor(&data)                                // 200 + application/cbor
reply().redirect("/new-location", Some(302))       // 302 redirect
reply().redirect("/new-location", None)            // 302 redirect (default)
reply().code(204).send(Vec::new())                 // 204 no body
reply().type_header("application/xml").send(xml_bytes)  // custom content type
```

Multiple Set-Cookie headers are supported via `.header()`:

```rust,ignore
reply()
    .header("set-cookie", "a=1; Path=/")
    .header("set-cookie", "b=2; Path=/")
    .json(json!({"ok": true}))
```

## Layer 3: Macros (Deprecated)

Deprecated. Prefer `reply()` or the free functions (`ok()`, `created()`, etc.).

### ok_json!

```rust,ignore
ok_json!({"key": "value", "count": 42})   // inline JSON object -- prefer ok(json!({...}))
```

### created_json!

```rust,ignore
created_json!({"id": new_id})              // prefer reply().code(201).json(json!({...}))
```

### error_json!

```rust,ignore
error_json!(400, {"error": "Validation failed"})   // prefer reply().status(400).json(json!({...}))
```

### html! / text!

```rust,ignore
html!("<h1>Title</h1>")                    // prefer reply().html("...") or ok_html("...")
text!("plain response")                    // prefer reply().text("...") or ok_text("...")
```

JSON macros accept inline `json!`-style object syntax (they wrap `json!` internally).

## ResponseExt trait

Adds headers to any response or result:

```rust,ignore
pub trait ResponseExt {
    fn add_header(self, name: &str, value: &str) -> Self;
}
```

Works on both `Response<ResponseBody>` and `Result<Response<ResponseBody>>`:

```rust,ignore
ok_html(html).add_header("x-cache", "HIT")
ok(data).add_header("x-request-id", &id)
```

## Response headers via reply builder

```rust,ignore
resource!(Cached {
    get(ctx) => {
        reply()
            .header("x-cache", "HIT")
            .header("cache-control", "max-age=3600")
            .json(json!({"data": "cached"}))
    }
});
```

Or via `ResponseExt`:

```rust,ignore
resource!(Cached {
    get(ctx) => {
        ok(json!({"data": "cached"}))
            .add_header("x-cache", "HIT")
            .add_header("cache-control", "max-age=3600")
    }
});
```

## Decision Table

| Need | Use |
|------|-----|
| Simple JSON 200 | `ok(data)` |
| Simple JSON 201 | `created(data)` |
| No body (204) | `no_content()` |
| Pre-serialized JSON | `ok_json_bytes(bytes)` |
| Error with message | `bad_request(msg)`, `not_found(msg)`, `unauthorized(msg)` |
| Error with custom status | `error_response(422, msg)` |
| Error from YetiError | `structured_error_response(&err)` |
| Storage/serialization error | `storage_error(err)`, `serialization_error(err)` |
| Custom status + headers | `reply().code(201).header(...).json(data)` |
| Inside `resource!` macro | `ok_json!({...})`, `created_json!({...})` |
| HTML/text content | `ok_html(content)` or `html!(content)` |
| Redirect | `reply().redirect(url, Some(302))` |
| Binary formats | `reply().messagepack(data)` or `reply().cbor(data)` |
| CSV download | `reply().csv(csv_string)` |
| Custom MIME type | `ok_with_content_type(mime, data)` |
| Add header to any response | `.add_header("name", "value")` |
| Sync result as future | `ready(ok(data))` |
| Early error return (async) | `error_future(400, "message")` |

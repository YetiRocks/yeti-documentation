# Response Helpers

Three layers of response building, from simplest to most flexible.

## Layer 1: Free Functions

Return a response in one call. All return `Result<Response<ResponseBody>>`.

### Success responses

```rust,ignore
fn ok<T: Serialize>(data: T) -> Result<Response<ResponseBody>>
fn created<T: Serialize>(data: T) -> Result<Response<ResponseBody>>
fn created_with_location(id: &str) -> Result<Response<ResponseBody>>
fn no_content() -> Result<Response<ResponseBody>>
```

```rust,ignore
ok(json!({"status": "active"}))              // 200 + JSON
created(json!({"id": "new-123"}))            // 201 + JSON
created_with_location("abc-123")             // 201 + Location header
no_content()                                  // 204 empty
```

### Error responses

```rust,ignore
fn bad_request(message: &str) -> Result<Response<ResponseBody>>
fn not_found(message: &str) -> Result<Response<ResponseBody>>
fn unauthorized(message: &str) -> Result<Response<ResponseBody>>
fn internal_error(message: &str) -> Result<Response<ResponseBody>>
fn error<T: Serialize>(data: T) -> Result<Response<ResponseBody>>
fn error_response(status: u16, message: &str) -> Result<Response<ResponseBody>>
fn json_response<T: Serialize>(status: u16, data: T) -> Result<Response<ResponseBody>>
```

```rust,ignore
bad_request("Invalid email format")          // 400 + {"error": "..."}
not_found("User not found")                  // 404 + {"error": "..."}
unauthorized("Token expired")                // 401 + {"error": "..."}
internal_error("Database connection failed") // 500 + {"error": "..."}
error(json!({"field": "email", "msg": "required"}))  // 400 + custom JSON
error_response(422, "Validation failed")     // custom status + {"error": "..."}
json_response(200, json!({"custom": true}))  // custom status + JSON body
```

### Content type responses

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

```rust,ignore
fn record_not_found(key: &str) -> Result<Response<ResponseBody>>
fn missing_param(param: &str) -> Result<Response<ResponseBody>>
fn get_or_not_found(result: Result<Option<Vec<u8>>>, id: &str) -> StdResult<Vec<u8>, Box<Response<ResponseBody>>>
```

```rust,ignore
record_not_found("user-123")                 // 404: "Record not found: user-123"
missing_param("email")                       // 400: "Missing 'email' parameter"

// Pattern for raw storage lookups
let data = match get_or_not_found(backend.get(key).await, &id) {
    Ok(data) => data,
    Err(response) => return Ok(*response),
};
```

## Layer 2: Reply Builder

Chain methods for custom status codes, headers, and content types. Start with `reply()`.

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

## Layer 3: Macros

For inline use inside `resource!` blocks.

### ok_json!

```rust,ignore
ok_json!({"key": "value", "count": 42})   // inline JSON object
ok_json!(some_variable)                     // any serializable expression
```

### created_json!

```rust,ignore
created_json!({"id": new_id})
```

### error_json!

```rust,ignore
error_json!(400, {"error": "Validation failed"})
error_json!(422, {"errors": validation_errors})
```

### html! / text!

```rust,ignore
html!("<h1>Title</h1>")
text!("plain response")
```

The JSON macros accept both bare expressions and inline `json!`-style object syntax.

## ResponseExt trait

Add headers to any response or result:

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

## Response headers via context

Use `ctx.response_headers()` alongside any response helper:

```rust,ignore
resource!(Cached {
    get(request, ctx) => {
        ctx.response_headers().append("x-cache", "HIT");
        ctx.response_headers().set("cache-control", "max-age=3600");
        ok(json!({"data": "cached"}))
    }
});
```

## Decision Table

| Need | Use |
|------|-----|
| Simple JSON 200 | `ok(data)` |
| Simple JSON 201 | `created(data)` |
| No body (204) | `no_content()` |
| Error with message | `bad_request(msg)`, `not_found(msg)`, `unauthorized(msg)` |
| Error with custom status | `error_response(422, msg)` |
| Custom status + headers | `reply().code(201).header(...).json(data)` |
| Inside `resource!` macro | `ok_json!({...})`, `created_json!({...})` |
| HTML/text content | `ok_html(content)` or `html!(content)` |
| Redirect | `reply().redirect(url, Some(302))` |
| Binary formats | `reply().messagepack(data)` or `reply().cbor(data)` |
| CSV download | `reply().csv(csv_string)` |
| Custom MIME type | `ok_with_content_type(mime, data)` |
| Add header to any response | `.add_header("name", "value")` |

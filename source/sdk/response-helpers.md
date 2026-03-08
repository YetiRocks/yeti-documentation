# Response Helpers

Three layers, from simplest to most flexible.

## Layer 1: Free Functions

Return a response in one call:

```rust,ignore
ok(json!({"status": "active"}))              // 200 OK + JSON
created(json!({"id": "new-123"}))            // 201 Created + JSON
no_content()                                  // 204 No Content
not_found(json!({"error": "missing"}))       // 404 Not Found + JSON
bad_request(json!({"error": "invalid"}))     // 400 Bad Request + JSON
unauthorized()                                // 401 Unauthorized
internal_error(json!({"error": "failed"}))   // 500 Internal Error + JSON
error_response(422, json!({"error": "..."})) // Custom error code + JSON
ok_html("<h1>Hello</h1>")                    // 200 OK + HTML
ok_text("plain text")                        // 200 OK + text/plain
```

## Layer 2: Reply Builder

Chain methods for custom status codes, headers, and content types:

```rust,ignore
reply().json(data)                                // 200 + JSON (default)
reply().code(201).json(data)                      // 201 + JSON
reply().code(201).header("x-id", &id).json(data)  // 201 + custom header + JSON
reply().html(content)                              // 200 + HTML
reply().text(content)                              // 200 + text/plain
reply().csv(csv_string)                            // 200 + text/csv
reply().messagepack(data)                          // 200 + MessagePack
reply().cbor(data)                                 // 200 + CBOR
reply().redirect("/new-location", Some(302))       // 302 redirect
reply().code(204).empty()                          // 204 no body
```

## Layer 3: Macros

For inline use inside `resource!` blocks:

```rust,ignore
ok_json!({"key": "value", "count": 42})
ok_json!(some_variable)

created_json!({"id": new_id})

error_json!(400, {"error": "Validation failed"})

html!("<h1>Title</h1>")

text!("plain response")
```

The JSON macros accept bare expressions (`ok_json!(data)`) or inline object syntax (`ok_json!({"key": "value"})`).

## Decision Table

| Need | Use |
|------|-----|
| Simple JSON response | `ok(data)` |
| Custom status + headers | `reply().code(201).header(...).json(data)` |
| Inside resource! macro | `ok_json!({ "key": "value" })` |
| HTML/text content | `reply().html(content)` or `html!(content)` |
| Redirect | `reply().redirect("/new", Some(302))` |
| MessagePack/CBOR | `reply().messagepack(data)` or `reply().cbor(data)` |
| CSV download | `reply().csv(csv_string)` |
| No body (204) | `no_content()` |
| Error with status | `error_response(422, json!({...}))` |

## Custom Response Headers

Use `ctx.response_headers()` alongside any response helper:

```rust,ignore
resource!(Cached {
    get(request, ctx) => {
        ctx.response_headers().append("x-cache", "HIT");
        ctx.response_headers().append("cache-control", "max-age=3600");
        ok(json!({"data": "cached"}))
    }
});
```

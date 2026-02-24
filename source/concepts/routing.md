# Routing & Endpoints

Yeti generates routes automatically from schemas and resources. Every `@export`ed table and every resource file produces HTTP endpoints under the app's URL prefix.

## URL Structure

```
https://localhost:9996/{app-id}/{resource-or-table}
```

## Custom Resources Override Tables

A resource with the same name as a table takes precedence:

```rust
resource!(Users {
    post(req, ctx) => {
        let mut body: serde_json::Value = req.json()?;
        body["createdAt"] = json!(unix_timestamp()?);
        let table = ctx.get_table("User")?;
        table.post(None, body.clone()).await?;
        created(body)
    }
});
```

Unoverridden methods fall through to the default table handler.

## Default Resources

A default resource catches all unmatched paths:

```rust
resource!(SpaFallback {
    default = true,
    get => ok_html(include_str!("../web/index.html"))
});
```

One default resource per application.

## Route Priority

1. Custom resources (exact name match)
2. Table endpoints
3. Default resource (catch-all)
4. Static files
5. 404 Not Found

## See Also

- [REST API](../api/rest.md) - Endpoint reference, query parameters, FIQL
- [Custom Resources](../guides/custom-resources.md) - Full resource API
- [Static File Serving](../guides/static-files.md) - Serving frontend apps

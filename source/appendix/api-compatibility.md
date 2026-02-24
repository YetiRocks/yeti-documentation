# API Compatibility Matrix

Harper API implementation status in Yeti. ~95% parity achieved.

## Resource API (REST)

| Endpoint | Status |
|----------|--------|
| `GET /schema/table` | Complete |
| `GET /schema/table/:id` | Complete |
| `POST /schema/table` | Complete |
| `PUT /schema/table/:id` | Complete |
| `DELETE /schema/table/:id` | Complete |
| `GET /schema/table?fiql` | Complete |

## FIQL Query Language

| Feature | Status |
|---------|--------|
| Equality (`==`, `!=`) | Complete |
| Comparison (`>`, `>=`, `<`, `<=`, `=gt=`, `=ge=`, `=lt=`, `=le=`) | Complete |
| Wildcards (`*name*`) | Complete |
| AND/OR (`&`, `\|`) | Complete |
| Grouping, NOT | Complete |
| Null handling | Complete |
| Regex (`=~=`) | Complete |
| Set membership (`=in=`, `=out=`) | Complete |
| Full-text search (`=ft=`) | Complete |
| Strict equality (`===`, `!==`) | Yeti extension |
| Contains/starts/ends (`=ct=`, `=sw=`, `=ew=`) | Yeti extension |
| Range operators (`=gele=`, `=gtlt=`) | Yeti extension |
| Type prefixes (`number:`, `boolean:`, `date:`) | Yeti extension |

## Operations API

| Operation | Status |
|-----------|--------|
| `system_information` | Complete |
| `health_check` | Complete |
| `get_configuration` | Complete |
| `get_components` / `list_apps` | Complete |
| `describe_all` / `describe_table` | Complete |
| `package_component` / `deploy_component` | Complete |
| `add_component` / `drop_component` | Planned |
| Schema operations (`create_schema`, `create_table`, etc.) | Planned |

## Other Features

| Feature | Status |
|---------|--------|
| Hash/range/full-text/composite indexes | Complete |
| HNSW vector index | Complete |
| Custom resources (GET/POST/PUT/DELETE/PATCH) | Complete |
| Static file serving | Complete |
| Auto-embedding (yeti-vectors) | Yeti extension |

## Legend

- **Complete** - Fully implemented and tested
- **Planned** - Scheduled for implementation
- **Yeti extension** - Feature beyond Harper's capabilities

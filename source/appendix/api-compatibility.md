# API Compatibility Matrix

Yeti API feature implementation status.

## Resource API (REST)

| Endpoint | Status |
|----------|--------|
| `GET /{app}/{table}` | Complete |
| `GET /{app}/{table}/:id` | Complete |
| `POST /{app}/{table}` | Complete |
| `PUT /{app}/{table}/:id` | Complete |
| `DELETE /{app}/{table}/:id` | Complete |
| `GET /{app}/{table}?fiql` | Complete |

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
| Strict equality (`===`, `!==`) | Complete |
| Contains/starts/ends (`=ct=`, `=sw=`, `=ew=`) | Complete |
| Range operators (`=gele=`, `=gtlt=`) | Complete |
| Type prefixes (`number:`, `boolean:`, `date:`) | Complete |

## Administrative Endpoints

| Endpoint | Status |
|----------|--------|
| `GET /health` | Complete |
| `GET /yeti-applications/Application` | Complete (requires super_user) |
| `GET /yeti-auth/users` | Complete (requires super_user) |
| `GET /yeti-auth/roles` | Complete (requires super_user) |
| `GET /yeti-telemetry/Log` | Complete (requires super_user) |
| `GET /yeti-ai/AiModel` | Complete (requires super_user) |

## Other Features

| Feature | Status |
|---------|--------|
| Hash/range/full-text/composite indexes | Complete |
| HNSW vector index | Complete |
| Custom resources (GET/POST/PUT/DELETE/PATCH) | Complete |
| Static file serving | Complete |
| Server-Sent Events (SSE) | Complete |
| WebSocket subscriptions | Complete |
| MQTT publish/subscribe | Complete |
| GraphQL queries | Complete |
| Auto-embedding (yeti-ai) | Complete |
| OAuth 2.0 (Google, GitHub, Microsoft) | Complete |
| JWT authentication | Complete |
| Role-based access control | Complete |

## Legend

- **Complete** - Fully implemented and tested

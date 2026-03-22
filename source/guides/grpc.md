# gRPC API

Yeti exposes a gRPC Tables service alongside the REST, GraphQL, and other interfaces. gRPC clients connect to the same port as HTTP — Yeti routes HTTP/2 requests with `content-type: application/grpc` to the gRPC handler, while all other requests go to the normal HTTP router.

## Enabling gRPC

gRPC is enabled by default in `yeti-config.yaml`:

```yaml
interfaces:
  grpc:
    enabled: true
```

Per-table control is available via the `@export` directive in your schema:

```graphql
# gRPC enabled (default when @export is present)
type Product @table @export {
  id: ID! @primaryKey
  name: String!
  price: Float!
}

# gRPC explicitly disabled for this table
type InternalLog @table @export(grpc: false) {
  id: ID! @primaryKey
  message: String!
  timestamp: Float!
}
```

Tables without `@export` are not exposed over any interface (REST, GraphQL, gRPC, etc.).

## Proto Service Definition

The Tables service is defined in `tables.proto`:

```protobuf
syntax = "proto3";
package yeti.tables;

service Tables {
  rpc Get(GetRequest) returns (GetResponse);
  rpc Put(PutRequest) returns (PutResponse);
  rpc Delete(DeleteRequest) returns (DeleteResponse);
  rpc Scan(ScanRequest) returns (ScanResponse);
  rpc Query(QueryRequest) returns (QueryResponse);
  rpc ListTables(ListTablesRequest) returns (ListTablesResponse);
  rpc Subscribe(ScanRequest) returns (stream Record);
}

message Record {
  string key = 1;
  bytes value = 2;   // JSON-encoded
}

message GetRequest {
  string app_id = 1;
  string table = 2;
  string key = 3;
}

message GetResponse {
  bool found = 1;
  bytes value = 2;   // JSON-encoded
}

message PutRequest {
  string app_id = 1;
  string table = 2;
  string key = 3;
  bytes value = 4;   // JSON-encoded
}

message PutResponse {}

message DeleteRequest {
  string app_id = 1;
  string table = 2;
  string key = 3;
}

message DeleteResponse {}

message ScanRequest {
  string app_id = 1;
  string table = 2;
  string prefix = 3;
  uint32 limit = 4;
}

message ScanResponse {
  repeated Record records = 1;
}

message QueryRequest {
  string app_id = 1;
  string table = 2;
  string fiql = 3;    // FIQL filter expression
  uint32 limit = 4;
  uint32 offset = 5;
}

message QueryResponse {
  repeated bytes records = 1;  // JSON-encoded records
  uint32 total = 2;
}

message ListTablesRequest {
  string app_id = 1;
}

message ListTablesResponse {
  repeated string tables = 1;
}
```

All `value` fields use JSON encoding. When writing via `Put`, send a JSON-encoded byte array. When reading via `Get`, `Scan`, or `Query`, the returned bytes are JSON.

## Operations

| RPC | Description |
|-----|-------------|
| `Get` | Retrieve a single record by key |
| `Put` | Create or update a record (upsert) |
| `Delete` | Remove a record by key |
| `Scan` | List records matching a key prefix, with optional limit |
| `Query` | Filter records using a FIQL expression, with pagination |
| `ListTables` | List all table names for an application |
| `Subscribe` | Server-streaming RPC that pushes real-time changes via PubSub |

## Example Usage with grpcurl

Assuming Yeti is running on `localhost:9996` with an app called `my-api` that has a `Product` table:

### List Tables

```bash
grpcurl -plaintext \
  -d '{"app_id": "my-api"}' \
  localhost:9996 yeti.tables.Tables/ListTables
```

```json
{
  "tables": ["Product", "Category"]
}
```

### Create a Record

```bash
grpcurl -plaintext \
  -d '{
    "app_id": "my-api",
    "table": "Product",
    "key": "prod-001",
    "value": "{\"id\":\"prod-001\",\"name\":\"Widget\",\"price\":9.99}"
  }' \
  localhost:9996 yeti.tables.Tables/Put
```

### Read a Record

```bash
grpcurl -plaintext \
  -d '{"app_id": "my-api", "table": "Product", "key": "prod-001"}' \
  localhost:9996 yeti.tables.Tables/Get
```

```json
{
  "found": true,
  "value": "{\"id\":\"prod-001\",\"name\":\"Widget\",\"price\":9.99}"
}
```

### Scan with Prefix

```bash
grpcurl -plaintext \
  -d '{"app_id": "my-api", "table": "Product", "prefix": "prod-", "limit": 10}' \
  localhost:9996 yeti.tables.Tables/Scan
```

### Query with FIQL Filter

```bash
grpcurl -plaintext \
  -d '{
    "app_id": "my-api",
    "table": "Product",
    "fiql": "price=gt=5.00",
    "limit": 20,
    "offset": 0
  }' \
  localhost:9996 yeti.tables.Tables/Query
```

### Subscribe to Changes

```bash
grpcurl -plaintext \
  -d '{"app_id": "my-api", "table": "Product", "prefix": ""}' \
  localhost:9996 yeti.tables.Tables/Subscribe
```

This opens a server-streaming connection. Records are pushed as they change in real-time via the PubSub system.

### Delete a Record

```bash
grpcurl -plaintext \
  -d '{"app_id": "my-api", "table": "Product", "key": "prod-001"}' \
  localhost:9996 yeti.tables.Tables/Delete
```

## When to Use gRPC vs. REST

| Use Case | Recommended Interface |
|----------|----------------------|
| Browser or frontend clients | REST or GraphQL |
| Service-to-service communication | gRPC |
| Real-time subscriptions from backend services | gRPC `Subscribe` |
| Real-time subscriptions from browsers | SSE or WebSocket |
| Bulk data operations | gRPC (lower serialization overhead) |
| Ad-hoc queries and exploration | REST with FIQL, or GraphQL |
| AI agent integration | MCP |
| IoT devices | MQTT |

gRPC is best suited for backend service-to-service communication where you benefit from:

- **Strong typing** via protobuf schemas
- **Streaming** via `Subscribe` for real-time change feeds
- **Lower overhead** compared to JSON over HTTP for high-throughput scenarios
- **Code generation** for type-safe clients in any language

## TLS

When Yeti is configured with TLS, gRPC clients must use TLS as well. With grpcurl:

```bash
grpcurl \
  -cacert certs/localhost/rootCA.pem \
  -d '{"app_id": "my-api"}' \
  localhost:443 yeti.tables.Tables/ListTables
```

## Disabling gRPC

To disable gRPC entirely:

```yaml
interfaces:
  grpc:
    enabled: false
```

To disable gRPC for a specific table while keeping it enabled for others, use the `@export` directive:

```graphql
type PublicData @table @export(grpc: true) {
  id: ID! @primaryKey
  value: String!
}

type SensitiveData @table @export(grpc: false, rest: true) {
  id: ID! @primaryKey
  secret: String!
}
```

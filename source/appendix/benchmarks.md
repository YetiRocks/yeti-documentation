# Performance Benchmarks

Live benchmark results from a single Yeti node running the app-benchmarks application.

## End-to-End API Throughput

Results from 30-second tests with 100 concurrent clients (5s warmup excluded). All traffic over HTTPS/TLS 1.3.

### Transactional API (REST)

| Operation | Throughput | P50 | P95 | P99 |
|-----------|------------|-----|-----|-----|
| REST Reads | 87k req/s | 1.07 ms | 2.01 ms | 2.71 ms |
| REST Writes | 52k req/s | 1.74 ms | 3.44 ms | 6.42 ms |
| REST Update | 38k req/s | 2.31 ms | 4.62 ms | 8.51 ms |
| REST Join | 83k req/s | 1.07 ms | 2.08 ms | 2.88 ms |

### Graph API (GraphQL)

| Operation | Throughput | P50 | P95 | P99 |
|-----------|------------|-----|-----|-----|
| GraphQL Reads | 74k req/s | 1.22 ms | 2.54 ms | 3.74 ms |
| GraphQL Writes | 66k req/s | — | — | — |
| GraphQL Updates | — | — | — | — |
| GraphQL Join | — | — | — | — |

### Realtime & Streaming

| Test | Clients | Throughput | Description |
|------|---------|------------|-------------|
| WS Fan-In | 100 | 749k msg/s | WebSocket ingestion from concurrent writers |
| WS Fan-Out | 4.3k | 28k msg/s | WebSocket subscriber message delivery |
| SSE Fan-Out | 1k | 26k msg/s | SSE subscriber message delivery |
| MQTT Fan-Out | — | — | MQTT broker pub/sub throughput |

## Running Benchmarks

Benchmarks run as a standalone Yeti application at `/app-benchmarks/`. The web UI provides one-click test execution with live progress tracking.

```bash
# Access the benchmark dashboard
open https://localhost/app-benchmarks/
```

Individual load test binaries can also be run directly:

```bash
load-rest --test rest-read --base-url https://localhost --duration 30 --vus 100
load-graphql --test graphql-read --base-url https://localhost --duration 30 --vus 100
load-realtime --test ws --base-url https://localhost --duration 30 --vus 15000
```

## Test Environment

| Parameter | Value |
|-----------|-------|
| Duration | 30 seconds per test (5s warmup excluded) |
| Concurrency | 100 clients (API), up to 15,000 subscribers (realtime) |
| Transport | HTTPS / TLS 1.3, HTTP/1.1 with connection reuse |
| Storage | Embedded RocksDB (single node, no replication) |
| Dataset | 1,000 records for reads/joins |

## Bottleneck Analysis

1. **Writes**: Storage I/O and WAL throughput dominate write cost
2. **Reads**: Sub-millisecond with RocksDB block cache hits
3. **Realtime**: TLS handshake capacity limits concurrent connections (~15k per process)
4. **Indexes**: Only index fields you filter on — each index adds write overhead

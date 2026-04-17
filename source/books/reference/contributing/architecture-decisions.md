# Architecture Decisions

Key technology choices for yeti v1.0.

## ADR-001: RocksDB as Storage Backend

**Decision**: Embedded RocksDB for all deployments.

**Why**: LSM-tree architecture optimized for write-heavy workloads, proven at Facebook/LinkedIn/Netflix scale, native TTL support, efficient range queries. 10+ years in production.

**Rejected**: Sled (beta quality), LMDB (lower write throughput), SQLite (global write lock, unnecessary SQL overhead).

**Benchmarks**: Write 100K-400K ops/s, Read >500K ops/s, Scan 381K-430K ops/s.

## ADR-002: Rust

**Decision**: All components in Rust.

**Why**: Zero-cost abstractions, memory safety without GC pauses, predictable performance, single binary deployment.

**Rejected**: Go (GC latency spikes), C++ (memory safety concerns), Node.js (single-threaded, GC pauses).

**Benchmarks**: p50 <500us, p99 <5ms, no GC-related latency spikes.

## ADR-003: Axum for HTTP

**Decision**: Axum as HTTP framework.

**Why**: Tower-native middleware ecosystem, first-class WebSocket support, built-in TLS via rustls, strong async ergonomics, actively maintained by the Tokio team.

**Rejected**: Actix-web (macro-heavy API, separate runtime), Rocket (sync-first), Warp (smaller community).

## ADR-004: FIQL for Query Language

**Decision**: FIQL (Feed Item Query Language) for REST filtering.

**Why**: URL-safe, human-readable (`name==john;age>18`), composable with AND/OR operators, widely understood.

**Rejected**: OData (too complex), custom DSL (no user familiarity).

**Benchmarks**: Parse <1us per query, evaluate <100ns per record.

## ADR-005: No Backward Compatibility

**Decision**: v1.0 has no legacy support or migration paths from prior versions.

**Why**: Clean slate with no technical debt, single code path, simpler testing. Starting with v1.0, semantic versioning governs future compatibility.

## Technology Stack

| Component | Choice |
|-----------|--------|
| Language | Rust |
| Storage | RocksDB |
| HTTP Server | Axum |
| Query Language | FIQL |
| TLS | Rustls + ring |

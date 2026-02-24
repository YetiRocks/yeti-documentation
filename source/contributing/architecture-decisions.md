# Architecture Decisions

Key technology choices for yeti-core v1.0.

## ADR-001: RocksDB as Storage Backend

**Decision**: RocksDB for all deployments (embedded and cluster modes).

**Why**: LSM-tree architecture optimized for write-heavy workloads, proven at Facebook/LinkedIn/Netflix scale, native TTL support, efficient range queries. 10+ years in production.

**Rejected**: Sled (beta quality), LMDB (lower write throughput), SQLite (global write lock, unnecessary SQL overhead).

**Benchmarks**: Write 100K-400K ops/s, Read >500K ops/s, Scan 381K-430K ops/s.

## ADR-002: Rust

**Decision**: All components in Rust.

**Why**: Zero-cost abstractions, memory safety without GC pauses, predictable performance, single binary deployment.

**Rejected**: Go (GC latency spikes), C++ (memory safety concerns), Node.js (single-threaded, GC pauses).

**Benchmarks**: p50 <500us, p99 <5ms, no GC-related latency spikes.

## ADR-003: Actix-Web for HTTP

**Decision**: Actix-web as HTTP framework.

**Why**: Among fastest Rust web frameworks, built-in TLS via rustls, streaming support, WebSocket support, mature and battle-tested.

**Rejected**: Axum (less proven at the time), Rocket (sync-first), Warp (smaller community).

## ADR-004: FIQL for Query Language

**Decision**: FIQL (Feed Item Query Language) for REST filtering.

**Why**: Harper-compatible, URL-safe, human-readable (`name==john;age>18`), composable with AND/OR operators.

**Rejected**: OData (too complex), custom DSL (no user familiarity, breaks compatibility).

**Benchmarks**: Parse <1us per query, evaluate <100ns per record.

## ADR-005: No Backward Compatibility

**Decision**: v1.0 has no legacy support or migration paths from prior versions.

**Why**: Clean slate with no technical debt, single code path, simpler testing. Starting with v1.0, semantic versioning governs future compatibility.

## Technology Stack

| Component | Choice |
|-----------|--------|
| Language | Rust |
| Storage | RocksDB |
| HTTP Server | actix-web |
| Query Language | FIQL |
| TLS | Rustls + ring |
| Compatibility | Harper API |

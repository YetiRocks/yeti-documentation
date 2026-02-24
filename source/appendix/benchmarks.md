# Performance Benchmarks

Benchmark data from Yeti's Criterion.rs test suite. 8 threads, 20 iterations, 5-second measurement per benchmark. Test records: ~1KB with 8 attributes.

## Summary

| Operation | Throughput | Notes |
|-----------|------------|-------|
| Simple READ | 186K ops/s | Direct RocksDB access |
| Simple CREATE | 82K ops/s | No indexes |
| Mixed (70R/30W) | 156K ops/s | Realistic workload |
| With Indexes | 15-62K ops/s | Depends on index count |

## CRUD by Index Count

| Operation | 0 indexes | 1 index | 2 indexes |
|-----------|-----------|---------|-----------|
| CREATE | 82.5K | 25.4K (-69%) | 15.6K (-81%) |
| READ | 186.6K | 175K (-6%) | 172K (-8%) |
| UPDATE | 64.5K | 10.4K (-84%) | 5.7K (-91%) |
| DELETE | 32.9K | 9.7K (-71%) | 5.7K (-83%) |
| MIXED (70R/30W) | 156.2K | 62.0K (-60%) | 40.2K (-74%) |

## Full Stack

| Layer | Benchmark | Throughput |
|-------|-----------|------------|
| Encoding | key_encoding | 2.19M ops/s |
| Encoding | value_encoding | 7.60M ops/s |
| Storage | backend put | 845K ops/s |
| Storage | backend get | 821K ops/s |
| Indexes | hash insert | 14.1K ops/s |
| Indexes | hash lookup | 52.5K ops/s |
| Indexes | range scan | 5.13M ops/s |
| Query | fiql simple eq | 28.0M ops/s |
| Query | fiql 10k records | 43.4M ops/s |
| Handlers | 1k posts | 331K ops/s |
| Handlers | concurrent 8T | 807K ops/s |
| Handlers | mixed 70R/30W | 464K ops/s |
| Ingress | request deserialize (small) | 4.29M ops/s |
| Ingress | response serialize (small) | 11.4M ops/s |
| Ingress | full request cycle (8T) | 1.22M ops/s |
| Routing | GET 100 tables | 173K ops/s |
| Transaction | single write | 91.3K ops/s |
| Transaction | read-modify-write | 66.7K ops/s |
| Locking | acquire 1000 keys | 3.28M ops/s |
| Locking | contention 1 key | 4.02M ops/s |
| Static Files | serve 1000 files | 173K ops/s |

## Running Benchmarks

```bash
# Automated suite (recommended)
python3 run-benches.py

# Specific layer
python3 run-benches.py transaction

# Manual
cargo bench --bench integration

# Compare against baseline
cargo bench -- --save-baseline before-optimization
cargo bench -- --baseline before-optimization
```

## Bottleneck Analysis

1. **Writes**: Index updates (14-16K ops/s) dominate cost
2. **Reads**: RocksDB access (821K ops/s) with minimal overhead
3. **Overall**: Indexes are the main performance lever - only index fields you filter on

## Comparison

| System | Simple Read | Simple Write |
|--------|-------------|--------------|
| **Yeti** | 186K ops/s | 82K ops/s |
| Traditional DB | 5-10K ops/s | 3-5K ops/s |
| MongoDB | 10-20K ops/s | 5-10K ops/s |
| PostgreSQL | 15-30K ops/s | 10-15K ops/s |

Yeti's advantage: 10-20x faster due to zero network overhead and direct memory access.

# Performance Tuning

Start with defaults and adjust based on workload.

## Storage Tuning (RocksDB)

| Parameter | Default | Guidance |
|-----------|---------|----------|
| `cache_size_mb` | 2048 | Set to 10-20% of available RAM |
| `write_buffer_size_mb` | 512 | Increase for write-heavy workloads |
| `sync_writes` | true | Set `false` for 5-10x write throughput (trades durability) |
| `enable_compression` | false | Enable for 50-70% storage reduction with minimal CPU cost |

## HTTP Tuning

| Parameter | Default | Guidance |
|-----------|---------|----------|
| `maxInFlightRequests` | 10,000 | Increase for high concurrency |
| `maxConnectionRate` | 256 | Increase for high-traffic services |
| `keepAliveTimeout` | 75s | Reduce for stateless APIs |
| `compressionThreshold` | 1024 | Lower to compress more (trades CPU for bandwidth) |
| `timeout` | 60s | Reduce for fast-fail APIs |

## Thread Configuration

```yaml
threads:
  count: null    # null = auto-detect (CPU count)
```

Override only if sharing the machine with other services.

## Plugin Compilation

| Scenario | Time |
|----------|------|
| First build (cold cache) | ~2 min per plugin |
| Cached rebuild | ~10 seconds |

Use `--apps my-app` to load only the apps you need during development.

## Memory Estimates

```
(cache_size_mb + write_buffer_size_mb) * num_databases
+ maxInFlightRequests * 10KB + num_plugins * 15MB + ~100MB base
```

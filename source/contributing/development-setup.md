# Development Setup

## Prerequisites

- **Rust** 1.75+ (`rustup` recommended)
- **Git**
- **Docker** (optional, for cluster mode)

## Quick Start

```bash
git clone https://github.com/YetiRocks/yeti-core.git
cd yeti-core
cargo build --release
cargo test --workspace
```

## Development Commands

```bash
cargo check                          # Fast compile check
cargo test test_name -- --nocapture  # Run specific tests
cargo clippy --workspace             # Linting
cargo fmt --all                      # Formatting
cargo doc --no-deps --open           # Build docs
cargo bench                          # Benchmarks
```

## IDE Setup

VS Code: install `rust-analyzer`, `vscode-lldb`, `even-better-toml`.

```json
{
  "rust-analyzer.cargo.features": "all",
  "rust-analyzer.checkOnSave.command": "clippy"
}
```

## Running Applications

```bash
# Load all apps
yeti

# Load specific apps for faster startup
yeti --apps yeti-auth,my-app
```

## Environment Variables

```bash
export RUST_BACKTRACE=1              # Backtraces on panic
export RUST_LOG=debug                # Debug logging
export RUST_LOG=yeti_core=trace      # Trace for specific crate
```

## Project Structure

```
yeti-core/
├── Cargo.toml
├── src/
│   ├── main.rs
│   ├── lib.rs
│   ├── prelude.rs
│   ├── application/    # App loading, compiler
│   ├── auth/           # Auth pipeline
│   ├── backend/        # RocksDB, TiKV
│   ├── encoding/       # Key/value encoding
│   ├── extensions/     # Extension loading
│   ├── http/           # SSE, WebSocket
│   ├── indexes/        # Hash, range, HNSW
│   ├── operations/     # Operations API
│   ├── platform/       # TLS, telemetry, cluster
│   ├── query/          # FIQL, GraphQL
│   ├── resource/       # Resource trait, tables
│   ├── routing/        # Request dispatch
│   └── runtime/        # Server startup
├── benches/            # Criterion benchmarks
├── tests/              # Integration tests
└── docker/             # TiKV compose files
```

## Workflow

```bash
git checkout -b feature/my-feature
cargo check && cargo test && cargo clippy
cargo fmt --all
```

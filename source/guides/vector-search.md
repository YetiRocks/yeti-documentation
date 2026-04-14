# Vector Search

Built-in HNSW vector indexing for approximate nearest-neighbor search, powered by the yeti-ai service with a Candle-based inference backend.

## Schema

Use the `Vector` type to define an embedding field:

```graphql
type Document @table @export {
    id: ID! @primaryKey
    title: String!
    content: String
    embedding: Vector @indexed(source: "content")
}
```

The `Vector` type automatically creates an HNSW index. With `source` specified, embeddings auto-generate from the source field on every write:

```bash
curl -sk -X POST https://localhost:9996/my-app/Document \
  -H "Content-Type: application/json" \
  -d '{"id":"doc-1","title":"Intro to ML","content":"Machine learning is a branch of AI..."}'
```

The `embedding` field is populated automatically.

### Model Selection

The embedding model is resolved in this order:

1. **Schema field** - `@indexed(source: "content", model: "all-MiniLM-L6-v2")`
2. **App config** - `vectors: { model: "all-MiniLM-L6-v2" }`
3. **Default** - `BAAI/bge-small-en-v1.5` (downloaded on first use)

Most apps omit the model:

```graphql
embedding: Vector @indexed(source: "content")
```

### HNSW Tuning Parameters

Six HNSW parameters on `@indexed`:

```graphql
embedding: Vector @indexed(
    source: "content",
    distance: "cosine",
    optimizeRouting: 0.6,
    M: 32,
    efConstruction: 200,
    efSearchConstruction: 100,
    mL: 0.3
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `distance` | `"cosine"` | Distance metric: `"cosine"` or `"euclidean"` |
| `optimizeRouting` | `0.5` | Routing optimization aggressiveness (0.0-1.0) |
| `M` | `16` | Max connections per node per layer |
| `efConstruction` | `100` | Candidate list size during index construction |
| `efSearchConstruction` | `50` | Candidate list size during search |
| `mL` | `1/ln(M)` | Level generation normalization factor |

If `M` is set without `mL`, the value is auto-computed as `1/ln(M)`.

### Config.yaml Setup

yeti-ai auto-detects from `Vector` fields with `@indexed(source: ...)`. To set a default model:

```yaml
vectors:
  model: all-MiniLM-L6-v2
```

## Search

### JSON Query (recommended)

Use the `?query=` parameter with a JSON object. Vector search uses `"op": "vector"`:

```bash
curl -sk "https://localhost:9996/my-app/Document/?query=\
{\"conditions\":[{\"field\":\"embedding\",\"op\":\"vector\",\"value\":\"how does deep learning work\"}],\"limit\":5}"
```

The model and field configuration come from the schema -- the query only needs the search text.

Results are sorted by distance (nearest first) and include a `$distance` field:

```json
[
  {"id": "doc-1", "title": "Intro to ML", "content": "...", "$distance": 0.042},
  {"id": "doc-3", "title": "Deep Learning", "content": "...", "$distance": 0.187}
]
```

### Combined Filters

Mix vector search with FIQL conditions in the same query:

```bash
# Find articles about ML in the "science" category
curl -sk "https://localhost:9996/my-app/Document/?query=\
{\"conditions\":[\
{\"field\":\"embedding\",\"op\":\"vector\",\"value\":\"machine learning\"},\
{\"field\":\"category\",\"op\":\"==\",\"value\":\"science\"}\
],\"limit\":10}"
```

Vector search runs first (returns top-K by similarity), then FIQL conditions filter the results.

## yeti-ai Service

Embedding generation and local inference, backed by the Candle ML framework.

### Capabilities

- **Embeddings** -- `CandleVectorHook` implements the `VectorHook` trait for text and image embedding
- **Inference** -- `CandleAiHook` implements the `AiHook` trait for text completion, chat, and structured JSON output
- **Model management** -- Download, load, unload, and remove GGUF models via REST API
- **Hardware acceleration** -- MKL (Intel), CUDA (NVIDIA), and Metal (Apple Silicon) support

### Model Management API

All endpoints require `super_user` role.

```bash
# List available models
curl -sk https://localhost:9996/yeti-ai/models

# Download an inference model from HuggingFace
curl -sk -X POST https://localhost:9996/yeti-ai/download \
  -H "Content-Type: application/json" \
  -d '{"repo":"TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF","filename":"tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"}'

# Download an embedding model
curl -sk -X POST https://localhost:9996/yeti-ai/download \
  -H "Content-Type: application/json" \
  -d '{"repo":"BAAI/bge-small-en-v1.5","type":"embedding"}'

# Load a model into memory
curl -sk -X POST https://localhost:9996/yeti-ai/load \
  -H "Content-Type: application/json" \
  -d '{"model":"tinyllama-1.1b-chat-v1.0.Q4_K_M"}'

# Unload the current model
curl -sk -X POST https://localhost:9996/yeti-ai/unload

# Remove a model from disk
curl -sk -X POST https://localhost:9996/yeti-ai/remove \
  -H "Content-Type: application/json" \
  -d '{"model":"tinyllama-1.1b-chat-v1.0.Q4_K_M"}'

# Service status
curl -sk https://localhost:9996/yeti-ai/status
```

### VectorHook Trait

The `VectorHook` trait provides embedding methods (all sync -- call via `spawn_blocking`):

```rust,ignore
// Convert text to a vector
hook.vectorize_text("how does deep learning work", "BAAI/bge-small-en-v1.5")
    -> Result<Vec<f32>>

// Embed fields in a record based on mappings
hook.vectorize_fields(record, &mappings)
    -> Result<serde_json::Value>

// Convert raw image bytes to a vector
hook.vectorize_image(&image_bytes, "clip-ViT-B-32")
    -> Result<Vec<f32>>

// Check if a model is available
hook.validate_model("BAAI/bge-small-en-v1.5")
    -> Result<()>
```

### AiHook Trait

The `AiHook` trait provides local inference:

```rust,ignore
// Single-turn text completion
hook.complete("Explain quantum computing in one sentence", 100)
    -> Result<String>

// Multi-turn chat
hook.chat(&[("user", "What is Rust?"), ("assistant", "A systems language."), ("user", "Why use it?")], 200)
    -> Result<String>

// Structured JSON output
hook.complete_json("List 3 colors as a JSON array", 100)
    -> Result<serde_json::Value>

// List available models
hook.models() -> Vec<ModelInfo>
```

## Backfill

Adding vector fields to an existing app (or adding `source` to a `Vector` field) auto-backfills embeddings on next restart. The backfill is:

- **Non-blocking** -- runs as a background task after startup
- **Idempotent** -- skips records that already have embeddings
- **Progressive** -- logs progress every 100 records

## Supported Embedding Models

| Model | Type | Dimensions | Size |
|-------|------|------------|------|
| `BAAI/bge-small-en-v1.5` | Text | 384 | ~130 MB |
| `BAAI/bge-base-en-v1.5` | Text | 768 | ~440 MB |
| `BAAI/bge-large-en-v1.5` | Text | 1024 | ~1.3 GB |
| `all-MiniLM-L6-v2` | Text | 384 | ~80 MB |
| `clip-ViT-B-32` | Image | 512 | ~300 MB |

Models download to `{rootDirectory}/models/` on first use. Additional models available via the model management API.

## Embedding Cache

yeti-ai caches embeddings keyed by `sha256(model + "\0" + text)`. Deterministic, no TTL.

Disable per-app:

```yaml
vectors:
  cache: false
```

## See Also

- [FIQL Queries](fiql.md) - Text-based filtering
- [Schema Directives](../reference/schema-directives.md) - Full directive reference

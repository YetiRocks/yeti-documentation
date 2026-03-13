# Vector Search

Yeti includes built-in HNSW vector indexing for approximate nearest-neighbor search.

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

The `Vector` type automatically creates an HNSW index. When `source` is specified, Yeti auto-generates embeddings from the source field on every write - insert your text:

```bash
curl -sk -X POST https://localhost:9996/my-app/document \
  -H "Content-Type: application/json" \
  -d '{"id":"doc-1","title":"Intro to ML","content":"Machine learning is a branch of AI..."}'
```

The `embedding` field is populated automatically.

### Model Selection

The embedding model is resolved in this order:

1. **Schema field** - `@indexed(source: "content", model: "all-MiniLM-L6-v2")`
2. **App config** - `vectors: { model: "all-MiniLM-L6-v2" }`
3. **Default** - `BAAI/bge-small-en-v1.5` (ships with Yeti, downloaded on first use)

Most apps don't need to specify a model:

```graphql
embedding: Vector @indexed(source: "content")
```

### HNSW Tuning Parameters

All six HNSW algorithm parameters can be set on `@indexed`:

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
| `optimizeRouting` | `0.5` | Routing optimization aggressiveness (0.0–1.0) |
| `M` | `16` | Max connections per node per layer |
| `efConstruction` | `100` | Candidate list size during index construction |
| `efSearchConstruction` | `50` | Candidate list size during search |
| `mL` | `1/ln(M)` | Level generation normalization factor |

If `M` is set without `mL`, the value is auto-computed as `1/ln(M)`.

### Config.yaml Setup

The yeti-vectors extension is auto-detected when your schema has `@vector` fields. To enable it explicitly or set a default model:

```yaml
vectors:
  model: all-MiniLM-L6-v2
```

The older `extensions: - yeti-vectors:` format still works but is deprecated.

## Search

### JSON Query (recommended)

Use the `?query=` parameter with a JSON object. Vector search uses `"op": "vector"`:

```bash
curl -sk "https://localhost:9996/my-app/document/?query=\
{\"conditions\":[{\"field\":\"embedding\",\"op\":\"vector\",\"value\":\"how does deep learning work\"}],\"limit\":5}"
```

The model and field configuration come from the schema - the query only needs the search text.

Results are sorted by distance (nearest first) and include a `$distance` field:

```json
[
  {"id": "doc-1", "title": "Intro to ML", "content": "...", "$distance": 0.042},
  {"id": "doc-3", "title": "Deep Learning", "content": "...", "$distance": 0.187}
]
```

### Combined Filters

Vector search conditions can be mixed with FIQL conditions in the same query:

```bash
# Find articles about ML in the "science" category
curl -sk "https://localhost:9996/my-app/document/?query=\
{\"conditions\":[\
{\"field\":\"embedding\",\"op\":\"vector\",\"value\":\"machine learning\"},\
{\"field\":\"category\",\"op\":\"==\",\"value\":\"science\"}\
],\"limit\":10}"
```

Vector search runs first (returns top-K by similarity), then FIQL conditions filter the results.

### Manual Vector Search

For raw vector queries (without auto-embedding), pass the vector directly:

```bash
curl -sk "https://localhost:9996/my-app/document/?query=\
{\"conditions\":[{\"field\":\"embedding\",\"op\":\"vector\",\"value\":\"search text\"}],\"limit\":5}"
```

## Vector Search in Custom Resources

Custom resources access tables via yeti-sdk.

### Example: Semantic Search Resource

```rust,ignore
use yeti_sdk::prelude::*;

#[yeti_resource(name = "semantic-search")]
pub struct SemanticSearch;

impl Resource for SemanticSearch {
    fn get(&self, ctx: ResourceParams) -> ResourceFuture {
        let query = ctx.get("q").unwrap_or("").to_string();
        let limit: usize = ctx.get("limit")
            .and_then(|s| s.parse().ok())
            .unwrap_or(5);

        let hook = ctx.vector_hook().cloned();

        Box::pin(async move {
            let Some(hook) = hook else {
                return error_response(500, "Vector hook not available");
            };

            // Convert text query to vector
            let query_clone = query.clone();
            let vector = tokio::task::spawn_blocking(move || {
                hook.vectorize_text(&query_clone, "BAAI/bge-small-en-v1.5")
            }).await
              .map_err(|e| format!("Vectorization failed: {e}"))?
              .map_err(|e| format!("Embedding error: {e}"))?;

            ok(json!({
                "query": query,
                "vector_dims": vector.len()
            }))
        })
    }
}
```

### Vector Hooks from ResourceParams

| Method | Returns | Description |
|--------|---------|-------------|
| `ctx.vector_hook()` | `Option<&Arc<dyn VectorHook>>` | The embedding hook (from yeti-vectors) |
| `ctx.vector_mappings()` | `&[FieldMapping]` | Configured source-to-target field mappings |
| `ctx.vector_cache()` | `Option<&Arc<dyn KvBackend>>` | Embedding cache backend |
| `ctx.vector_batcher()` | `Option<&Arc<VectorBatcher>>` | Micro-batcher for batch embedding |

### VectorHook Methods

The `VectorHook` trait provides embedding methods (all sync - call via `spawn_blocking`):

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

## Image Embedding

Use a CLIP model for image vectors:

```graphql
type Photo @table @export {
    id: ID! @primaryKey
    thumbnail: String
    imageEmbedding: Vector @indexed(source: "thumbnail", model: "clip-ViT-B-32")
}
```

## Backfill

Adding yeti-vectors to an existing app (or adding `source` to a `Vector` field) auto-backfills embeddings on next restart. The backfill is:

- **Non-blocking** - runs as a background task after startup
- **Idempotent** - skips records that already have embeddings
- **Progressive** - logs progress every 100 records

If the schema declares `source` fields but yeti-vectors is not enabled, an error is logged and the app fails to load.

## Supported Models

| Model | Type | Dimensions | Size |
|-------|------|------------|------|
| `BAAI/bge-small-en-v1.5` | Text | 384 | ~130 MB |
| `BAAI/bge-base-en-v1.5` | Text | 768 | ~440 MB |
| `BAAI/bge-large-en-v1.5` | Text | 1024 | ~1.3 GB |
| `all-MiniLM-L6-v2` | Text | 384 | ~80 MB |
| `clip-ViT-B-32` | Image | 512 | ~300 MB |

The default model (`BAAI/bge-small-en-v1.5`) downloads automatically on first use to `{rootDirectory}/models/`. Additional models can be managed via the yeti-vectors admin UI.

## Embedding Cache

yeti-vectors caches embeddings keyed by `sha256(model + "\0" + text)`. Deterministic, no TTL.

Disable per-app:

```yaml
vectors:
  cache: false
```

Manage via REST:

```bash
# List cached embeddings
curl -sk https://localhost:9996/yeti-vectors/EmbeddingCache

# Delete a cached embedding
curl -sk -X DELETE https://localhost:9996/yeti-vectors/EmbeddingCache/{id}
```

## See Also

- [FIQL Queries](fiql.md) - Text-based filtering
- [Schema Directives](../reference/schema-directives.md) - Full directive reference

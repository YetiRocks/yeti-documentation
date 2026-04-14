# AI & Inference

Yeti embeds a Candle-based ML runtime for local embeddings and inference. No external API calls. No data exfiltration. Models download from HuggingFace Hub and run in-process.

## Auto-Embedding

Add a `Vector` field with `@indexed(source:)` to any table:

```graphql
type Document @table @export {
  id: ID! @primaryKey
  content: String!
  embedding: Vector @indexed(source: "content")
}
```

Embeddings generate automatically on write:

```bash
curl -X POST https://localhost:9996/my-app/Document \
  -H 'Content-Type: application/json' \
  -d '{"content": "Yeti runs everything in a single binary"}'
```

The yeti-ai service populates the `embedding` field using the configured model.

## Vector Search

Query by similarity with FIQL or JSON:

```bash
# FIQL — search by text similarity
curl 'https://localhost:9996/my-app/Document?filter=embedding=vector="single binary deployment"&limit=5'
```

Results are ranked by cosine similarity. The HNSW index provides sub-millisecond lookups at any dataset size.

## Local Inference

The yeti-ai service provides chat completion and text generation via the `AiHook` trait. AI hooks register at the service level (`RegistrationContext::add_ai_hook()`) and are not directly accessible from resource handler context. Expose inference to application code by building a service that wraps the `AiHook`:

```rust,ignore
// In a service's register():
ctx.add_ai_hook(Arc::new(MyAiHook::new()));

// AiHook methods are sync (no .await) for dylib boundary safety:
let response = ai_hook.complete("Summarize this:", 256)
    .map_err(|e| YetiError::Internal(e))?;
```

### Supported Operations

| Method | Description |
|--------|-------------|
| `complete(prompt, max_tokens)` | Single-turn text completion |
| `chat(messages, max_tokens)` | Multi-turn conversation |
| `complete_json(prompt, max_tokens)` | Structured JSON output |
| `models()` | List available models |
| `is_loaded(model)` | Check if a model is loaded |

## Model Management

Models are managed through the yeti-ai REST API:

```bash
# List available models
curl https://localhost:9996/yeti-ai/models

# Download a model from HuggingFace
curl -X POST https://localhost:9996/yeti-ai/models \
  -d '{"id": "BAAI/bge-small-en-v1.5"}'

# Load into memory
curl -X POST https://localhost:9996/yeti-ai/models/load \
  -d '{"id": "BAAI/bge-small-en-v1.5"}'

# Unload from memory
curl -X POST https://localhost:9996/yeti-ai/models/unload \
  -d '{"id": "BAAI/bge-small-en-v1.5"}'
```

## Hardware Acceleration

Yeti-ai detects available hardware and uses the fastest backend:

| Platform | Backend | Flag |
|----------|---------|------|
| Apple Silicon | Metal GPU | `--features metal` (default on macOS) |
| Intel CPU | MKL BLAS | `--features mkl` (separate binary) |
| NVIDIA GPU | CUDA | `--features cuda` (separate binary) |
| Any CPU | Candle native | Default (no flag needed) |

## Multi-Tenant Isolation

- **Public models** in `{root}/models/` — shared across all apps
- **Custom models** in `{root}/deployments/{hash}/models/` — per-deployment isolation

## See Also

- [Vector Search](vector-search.md) — Query patterns and index configuration
- [Schema Directives](../reference/schema-directives.md) — `@indexed` directive reference
- [Service API](../sdk/extension-api.md) — `AiHook` and `VectorHook` traits

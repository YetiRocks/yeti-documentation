# GraphQL

Yeti auto-generates a GraphQL API from your schema. Tables with `graphql: true` get query, mutation, and subscription support at `POST /{app-id}/graphql`.

## Enabling

```yaml
graphql: true
schemas:
  - schema.graphql
```

## Queries

```bash
# List all books
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Book { id title price genre } }"}'

# Nested relationships
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Book { title author { name } reviews { rating content } } }"}'
```

## Mutations

```bash
# Create
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { createAuthor(data: {id: \"author-new\", name: \"New Author\"}) { id name } }"}'

# Update
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { updateAuthor(id: \"author-new\", data: {name: \"Updated\"}) { id name } }"}'

# Delete
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { deleteAuthor(id: \"author-new\") { id } }"}'
```

## Variables

```bash
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation CreateBook($data: BookInput!) { createBook(data: $data) { id title } }",
    "variables": {"data": {"id":"book-new","title":"New Book","isbn":"978-0000000000","authorId":"author-1"}}
  }'
```

## Introspection

```bash
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } types { name kind } } }"}'
```

## Subscriptions via SSE

```bash
curl -sk -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "subscription { Book { id title price } }"}' \
  https://localhost:9996/graphql-explorer/graphql
```

## Explorer UI

The `graphql-explorer` app includes an interactive Apollo-style explorer at `https://localhost:9996/graphql-explorer/`.

## See Also

- [FIQL Queries](fiql.md) - REST-based filtering
- [Relationships & Joins](relationships.md) - Relationship directives
- [Server-Sent Events](sse.md) - SSE subscription details

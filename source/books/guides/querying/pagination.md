# Pagination & Sorting

## Pagination

```bash
# Limit results
curl -sk 'https://localhost:9996/graphql-explorer/Book?limit=10'

# Skip records
curl -sk 'https://localhost:9996/graphql-explorer/Book?offset=20'

# Page 2 (10 per page)
curl -sk 'https://localhost:9996/graphql-explorer/Book?limit=10&offset=10'

# Function-style: limit(offset, count)
curl -sk 'https://localhost:9996/graphql-explorer/Book?limit(10,10)'
```

## Sorting

```bash
# Ascending
curl -sk 'https://localhost:9996/graphql-explorer/Book?sort=title'

# Descending (prefix with -)
curl -sk 'https://localhost:9996/graphql-explorer/Book?sort=-price'

# Multi-field: sort by genre, then price descending within each genre
curl -sk 'https://localhost:9996/graphql-explorer/Book?sort=genre,-price'
```

## Combined

```bash
# Science fiction, sorted by price descending, page 2
curl -sk 'https://localhost:9996/graphql-explorer/Book?genre==Science%20Fiction&sort=-price&limit=10&offset=10'
```

## Pagination Strategy

| Use Case | Parameters |
|----------|-----------|
| First page | `?limit=25` |
| Next page | `?limit=25&offset=25` |
| Page N | `?limit=25&offset={(N-1)*25}` |
| Top 5 most expensive | `?sort=-price&limit=5` |

When fewer records than `limit` are returned, you've reached the last page.

## Tips

- Without `sort`, records return in storage order (typically insertion order)
- Null values sort last ascending, first descending
- For very large datasets with high offsets, consider cursor-based filtering on last seen ID

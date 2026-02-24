# FIQL Queries

FIQL (Feed Item Query Language) provides URI-friendly filtering on REST collection endpoints.

## Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `==` | Equals | `name==Widget` |
| `===` | Strict equals | `id===prod-001` |
| `!=` | Not equals | `category!=hardware` |
| `=gt=` / `>` | Greater than | `price=gt=10` |
| `=ge=` / `>=` | Greater or equal | `price=ge=10` |
| `=lt=` / `<` | Less than | `price=lt=20` |
| `=le=` / `<=` | Less or equal | `price=le=20` |
| `=ct=` | Contains | `name=ct=Widget` |
| `=sw=` | Starts with | `name=sw=Ultra` |
| `=ew=` | Ends with | `name=ew=Pro` |
| `=~=` | Regex | `name=~=^Ultra.*` |
| `=in=` | In set | `category=in=hardware,electronics` |
| `=out=` | Not in set | `category=out=food,clothing` |
| `=ft=` | Full-text search | `name=ft=ultra widget` |
| `=gele=` | Range (inclusive) | `price=gele=10,100` |
| `=gtlt=` | Range (exclusive) | `price=gtlt=10,100` |

Wildcards: `==Ultra*` (starts with), `==*Pro` (ends with), `==*Widget*` (contains).

## Logical Operators

| Operator | Meaning |
|----------|---------|
| `&` | AND |
| `\|` | OR |
| `!()` | NOT |

AND has higher precedence than OR. Use parentheses for grouping.

## Examples

```bash
# Equality
curl -sk 'https://localhost:9996/graphql-explorer/Book?genre==Mystery'

# Range
curl -sk 'https://localhost:9996/graphql-explorer/Book?price=ge=10&price=le=15'

# Set membership
curl -sk 'https://localhost:9996/graphql-explorer/Book?genre=in=Mystery,Romance'

# Regex
curl -sk 'https://localhost:9996/graphql-explorer/Book?title=~=^The'

# Negation
curl -sk 'https://localhost:9996/graphql-explorer/Book?!(price=gt=100)'

# Full-text search (AND semantics, all terms must match)
curl -sk 'https://localhost:9996/example-queries/Products?name=ft=ultra%20monitor'

# Combined: (Mystery OR Romance) AND price under $14
curl -sk 'https://localhost:9996/graphql-explorer/Book?(genre==Mystery|genre==Romance)&price=lt=14'

# With sorting, pagination, and field selection
curl -sk 'https://localhost:9996/graphql-explorer/Book?genre==Mystery&sort=-price&limit=5&select=title,price'
```

## Indexed vs Non-Indexed

FIQL works on all fields, but `@indexed` fields use secondary indexes for fast lookups. Non-indexed fields require table scans.

```graphql
type Book @table @export {
    id: ID! @primaryKey
    genre: String @indexed        # Fast filtering
    publishedYear: Int            # Scan-based (slower on large tables)
}
```

## URL Encoding

Special characters must be encoded: spaces as `%20`, `/` as `%2F`. Most HTTP libraries handle this automatically.

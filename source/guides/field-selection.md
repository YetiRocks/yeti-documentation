# Field Selection

The `select` parameter specifies which fields to return, reducing payload size.

## Usage

```bash
# Return only title and price
curl -sk 'https://localhost:9996/graphql-explorer/Book?select=title,price'
```

```json
[
  {"title": "Pride and Prejudice", "price": 12.99},
  {"title": "Foundation", "price": 15.99}
]
```

The primary key is not auto-included - add it explicitly if needed:

```bash
curl -sk 'https://localhost:9996/graphql-explorer/Book?select=id,title,price'
```

Function-style: `select(id,title,price)`

## Combined with Filters

```bash
# Mystery books, sorted by price, only title and price
curl -sk 'https://localhost:9996/graphql-explorer/Book?genre==Mystery&sort=-price&select=title,price'
```

Works on single records too:

```bash
curl -sk 'https://localhost:9996/graphql-explorer/Book/book-1?select=title,price,genre'
```

## Permissions

When RBAC attribute-level permissions are active, restricted fields are omitted regardless of `select`. No error is produced - the field is simply absent. Safe to use the same `select` for all users.

## Tips

- No `select=*` syntax - omit the parameter for all fields
- Field names are case-sensitive (match schema, typically camelCase)
- Invalid field names are silently ignored
- Selection reduces payload size but not storage reads

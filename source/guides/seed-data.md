# Seed Data & Data Loading

Load initial data into tables at startup from JSON files.

## JSON Format

```json
{
  "database": "graphql-explorer",
  "table": "Author",
  "records": [
    {"id": "author-1", "name": "Jane Austen", "email": "jane@austen.lit", "country": "England"},
    {"id": "author-2", "name": "Isaac Asimov", "email": "isaac@foundation.org", "country": "USA"}
  ]
}
```

| Field | Description |
|-------|-------------|
| `database` | Must match `@table(database: "...")` |
| `table` | Type name from schema (PascalCase) |
| `records` | Array of objects matching schema fields |

## Configuration

```yaml
dataLoader: data/*.json
```

One file per table, named in lowercase:

```
data/
  authors.json
  books.json
  categories.json
```

## Change Detection

Records are only written when the data file has changed since last load. Unchanged files are skipped for faster startup.

## Runtime Loading

### REST API

```bash
# Single record
curl -sk https://localhost:9996/my-app/Product -X POST \
  -H "Content-Type: application/json" \
  -d '{"id":"prod-1","name":"Widget","price":9.99}'

# Batch
curl -sk https://localhost:9996/my-app/Product -X POST \
  -H "Content-Type: application/json" \
  -d '[{"id":"prod-1","name":"Widget","price":9.99},{"id":"prod-2","name":"Gadget","price":19.99}]'
```

### CSV

```bash
curl -sk https://localhost:9996/my-app/Product -X POST \
  -H "Content-Type: text/csv" \
  -d 'id,name,price
prod-1,Widget,9.99
prod-2,Gadget,19.99'
```

## Tips

- Every record must include the primary key field
- `database` must match your `@table` directive (defaults to app_id if omitted)
- Field names are case-sensitive (match schema casing)
- Include foreign key values, not full related objects
- If table B references table A, load A first (alphabetical naming helps)

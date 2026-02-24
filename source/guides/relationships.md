# Relationships & Joins

The `@relationship` directive declares foreign key relationships for nested data retrieval in both GraphQL and REST.

## Patterns

### from - Many-to-One

Resolves a foreign key to the referenced record:

```graphql
type Book @table @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    authorId: ID! @indexed
    author: Author @relationship(from: "authorId")
}
```

`Book.authorId` --> find `Author` where `Author.id == Book.authorId`

### to - One-to-Many

Finds all records referencing this one:

```graphql
type Author @table @export(rest: true, graphql: true) {
    id: ID! @primaryKey
    name: String!
    books: [Book] @relationship(to: "authorId")
}
```

Find all `Book` where `Book.authorId == Author.id`

## GraphQL Queries

### Many-to-One

```bash
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Book { title price author { name country } publisher { name } } }"}'
```

### One-to-Many

```bash
curl -sk https://localhost:9996/graphql-explorer/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ Author { name books { title genre price } } }"}'
```

### Deep Nesting

```graphql
{
  Author {
    name
    books {
      title
      reviews {
        rating
        reviewer
      }
    }
  }
}
```

## REST API

Foreign key fields are always present. Traverse relationships with follow-up requests:

```bash
# Get book with authorId
curl -sk https://localhost:9996/graphql-explorer/Book/book-1

# Follow the relationship
curl -sk https://localhost:9996/graphql-explorer/Author/author-1

# One-to-many via filter
curl -sk 'https://localhost:9996/graphql-explorer/Book?authorId==author-1'
```

## Best Practices

- Always `@indexed` foreign key fields - without an index, `to` relationships require table scans
- Use GraphQL for nested data in a single request
- Keep nesting depth practical - `Author -> books -> author -> books` can be expensive
- Use `ID` (nullable) for optional relationships, `ID!` for required

# Your First Application

Build a task tracker with two related tables, seed data, a custom resource, and real-time streaming. Assumes you have completed [installation](installation.md) and the [Quickstart](quickstart.md).

## Step 1: Create the Application

```bash
mkdir ~/yeti/applications/task-tracker
mkdir ~/yeti/applications/task-tracker/resources
mkdir ~/yeti/applications/task-tracker/data
```

## Step 2: Write the Configuration

Create `~/yeti/applications/task-tracker/config.yaml`:

```yaml
name: "Task Tracker"
app_id: "task-tracker"
version: "1.0.0"
enabled: true
rest: true
graphql: true
schemas:
  path: schema.graphql
resources:
  path: "resources/*.rs"
dataLoader: data/*.json
```

## Step 3: Define the Schema

Create `~/yeti/applications/task-tracker/schema.graphql`:

```graphql
type Task @table(database: "task-tracker") @export(
    rest: true
    graphql: true
    sse: true
) {
    id: ID! @primaryKey
    title: String!
    description: String
    status: String! @indexed
    priority: String! @indexed
    assignee: String @indexed
    dueDate: String
    tagId: ID @indexed
    tag: Tag @relationship(from: "tagId")
    createdAt: String @createdTime
    updatedAt: String @updatedTime
}

type Tag @table(database: "task-tracker") @export(
    rest: true
    graphql: true
) {
    id: ID! @primaryKey
    name: String! @indexed
    color: String
    tasks: [Task] @relationship(to: "tagId")
}
```

| Directive | Purpose |
|-----------|---------|
| `@table(database: "...")` | Persistent table in the named database |
| `@export(rest: true, ...)` | Expose as REST, GraphQL, and/or SSE endpoints |
| `@primaryKey` | Record identifier |
| `@indexed` | Secondary index for FIQL filtering |
| `@relationship(from: "field")` | Foreign-key join (belongs-to) |
| `@relationship(to: "field")` | Reverse join (has-many) |

Full directive reference: [Schemas & Tables](../concepts/schemas.md).

## Step 4: Create a Custom Resource

Create `~/yeti/applications/task-tracker/resources/summary.rs`:

```rust,ignore
use yeti_sdk::prelude::*;

resource!(Summary {
    name = "summary",
    get(ctx) => {
        let tasks = ctx.get_table("Task")?;
        let total = tasks.count().await?;
        let by_status = tasks.count_by("status").await?;
        let by_priority = tasks.count_by("priority").await?;

        reply().json(json!({
            "total": total,
            "byStatus": by_status,
            "byPriority": by_priority,
        }))
    }
});
```

This registers `GET /task-tracker/summary`.

## Step 5: Add Seed Data

Create `~/yeti/applications/task-tracker/data/tags.json`:

```json
{
  "database": "task-tracker",
  "table": "Tag",
  "records": [
    { "id": "tag-bug", "name": "Bug", "color": "#e53e3e" },
    { "id": "tag-feature", "name": "Feature", "color": "#3182ce" },
    { "id": "tag-docs", "name": "Documentation", "color": "#38a169" }
  ]
}
```

Create `~/yeti/applications/task-tracker/data/tasks.json`:

```json
{
  "database": "task-tracker",
  "table": "Task",
  "records": [
    {
      "id": "task-001",
      "title": "Fix login redirect loop",
      "status": "in-progress",
      "priority": "high",
      "assignee": "alice",
      "tagId": "tag-bug"
    },
    {
      "id": "task-002",
      "title": "Add dark mode support",
      "status": "todo",
      "priority": "medium",
      "assignee": "bob",
      "tagId": "tag-feature"
    },
    {
      "id": "task-003",
      "title": "Write API reference docs",
      "status": "todo",
      "priority": "medium",
      "assignee": "alice",
      "tagId": "tag-docs"
    }
  ]
}
```

Seed data files require `database`, `table`, and `records`. Records load once on first startup when the table is empty.

## Step 6: Start the Server

```bash
yeti restart
```

First startup compiles the plugin (~2 minutes). Cached restarts take ~10 seconds.

## Step 7: Test It

```bash
# List all tasks
curl -sk https://localhost:9996/task-tracker/Task

# Filter: high priority tasks
curl -sk "https://localhost:9996/task-tracker/Task?priority==high"

# Filter: tasks not done, sorted by due date
curl -sk "https://localhost:9996/task-tracker/Task?status!=done&sort=-dueDate"

# Pagination
curl -sk "https://localhost:9996/task-tracker/Task?limit=2&offset=0"

# Include related tag data
curl -sk "https://localhost:9996/task-tracker/Task/task-001?select=id,title,tag%7Bname,color%7D"

# Custom resource
curl -sk https://localhost:9996/task-tracker/summary

# SSE stream
curl -sk --max-time 30 "https://localhost:9996/task-tracker/Task?stream=sse"
```

## Final Structure

```
~/yeti/applications/task-tracker/
  config.yaml          # App configuration
  schema.graphql       # Table definitions
  resources/
    summary.rs         # Custom resource
  data/
    tags.json          # Tag seed data
    tasks.json         # Task seed data
```

`@export`ed tables also support gRPC and MCP when those interfaces are enabled in `yeti-config.yaml`.

## Next Steps

- [Authentication](../guides/auth-overview.md) - Add Basic, JWT, or OAuth auth
- [Real-Time Features](../guides/realtime-overview.md) - SSE, WebSocket, PubSub
- [Building Services](../guides/building-extensions.md) - Shared services across apps
- [FIQL Queries](../guides/fiql.md) - Advanced filtering
Services](../guides/building-extensions.md) - Shared services across apps
- [FIQL Queries](../guides/fiql.md) - Advanced filtering

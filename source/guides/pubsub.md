# PubSub

PubSub is Yeti's internal publish/subscribe messaging system. It connects data changes to SSE and WebSocket streams. PubSub is in-process only - it powers real-time delivery but does not expose external endpoints.

## Architecture

```
                     PubSubManager
  ┌──────────────────────────────────────────┐
  │            Topics (HashMap)              │
  │                                          │
  │  "User"        -> broadcast::Sender      │
  │  "User/123"    -> broadcast::Sender      │
  │  "Message"     -> broadcast::Sender      │
  └──────────────────────────────────────────┘
           |                    |
     subscribe("User")   notify_update("User", "123", data)
           |                    |
           v                    v
    Receiver<Message>    Broadcasts to all subscribers
```

## Topics

| Topic | Scope | Example |
|-------|-------|---------|
| `"{Table}"` | Table-level | `"User"` - all User changes |
| `"{Table}/{id}"` | Record-level | `"User/123"` - changes to User 123 |
| Custom string | Application-level | `"notifications"` - custom events |

Record changes publish to **both** the record-level and table-level topics.

## Message Types

| Type | Description | Triggered By |
|------|-------------|--------------|
| `Update` | Record created or updated | POST, PUT |
| `Delete` | Record deleted | DELETE |
| `Publish` | Custom message | Application code |
| `Retained` | Historical data | Initial subscription |

```json
{
  "message_type": "Update",
  "data": { "id": "user-1", "name": "Alice" },
  "id": "user-1",
  "timestamp": "2025-06-15T10:30:00Z"
}
```

## Data Flow

```
REST PUT /User/123 {"name":"Updated"}
        |
        v
  TableResource::update()
        |
        v
  pubsub.notify_update("User", "123", data)
        |
        +----> "User/123" topic -> record-level subscribers
        |
        +----> "User" topic -> table-level subscribers
                    |
                    +----> SSE stream -> EventSource client
                    |
                    +----> WebSocket -> WS client
```

## Channel Capacity

Each topic uses a `tokio::sync::broadcast` channel with **256 message** capacity. Slow consumers that fall behind lose older messages. Use record-level subscriptions for high-throughput tables.

## Topic Lifecycle

- Topics are created lazily on first `subscribe()`
- Removed with `remove_topic()` when no longer needed
- `RwLock` ensures concurrent reads; exclusive access for new topic creation

## Custom Publish

```rust
pubsub.notify_publish("alerts", serde_json::json!({
    "severity": "warning",
    "message": "Disk usage above 80%"
})).await;
```

## API Reference

| Method | Description |
|--------|-------------|
| `subscribe(topic)` | Subscribe, returns a Receiver |
| `publish(topic, message)` | Send to all subscribers |
| `notify_update(table, id, data)` | Publish to record + table topics |
| `notify_delete(table, id)` | Publish deletion to both topics |
| `notify_publish(topic, data)` | Publish a custom message |
| `topic_count()` | Number of active topics |
| `subscriber_count(topic)` | Subscribers for a topic |
| `remove_topic(topic)` | Remove topic, drop subscribers |

## See Also

- [Real-Time Overview](realtime-overview.md) - All real-time features
- [Server-Sent Events](sse.md) - SSE delivery mechanism
- [WebSocket](websocket.md) - WebSocket delivery mechanism

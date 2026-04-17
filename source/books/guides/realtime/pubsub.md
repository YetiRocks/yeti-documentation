# PubSub

Yeti's internal publish/subscribe messaging backbone. SSE, WebSocket, and MQTT delivery all run on PubSub. Table writes automatically emit notifications; application code can subscribe or publish programmatically.

## Architecture

```
                     PubSubManager (DashMap)
  +----------------------------------------------+
  |               Topics                         |
  |                                              |
  |  "User"        -> broadcast::Sender (256)    |
  |  "User/123"    -> broadcast::Sender (256)    |
  |  "Message"     -> broadcast::Sender (256)    |
  |  "alerts"      -> broadcast::Sender (256)    |
  +----------------------------------------------+
           |                    |
     subscribe("User")   notify_update("User", "123", data)
           |                    |
           v                    v
    Receiver<Message>    Broadcasts to all subscribers
```

## Topics

| Topic | Scope | Example |
|-------|-------|---------|
| `"{Table}"` | Table-level | `"User"` -- all User changes |
| `"{Table}/{id}"` | Record-level | `"User/123"` -- changes to User 123 |
| Custom string | Application-level | `"alerts"` -- custom events |

Record changes publish to **both** the record-level and table-level topics automatically.

## Message Types

| Type | Description | Triggered By |
|------|-------------|--------------|
| `Update` | Record created or updated | `put()`, `patch()`, `create()`, `post()` |
| `Delete` | Record deleted | `delete()` |
| `Publish` | Custom message | `table.publish(id, message)` |
| `Retained` | Historical data | Initial subscription |

```json
{
  "message_type": "Update",
  "data": { "id": "user-1", "name": "Alice" },
  "id": "user-1",
  "timestamp": "2025-06-15T10:30:00Z"
}
```

## SDK API

Access PubSub through the `Table` struct returned by `context.tables().get("TableName")`.

### subscribe_all() -- All Table Changes

```rust,ignore
let tables = context.tables();
let table = tables.get("Message")?;

let mut rx = table.subscribe_all().await?;
while let Ok(msg) = rx.recv().await {
    println!("{:?} on {}", msg.message_type, msg.id.unwrap_or_default());
}
```

Returns a `broadcast::Receiver<SubscriptionMessage>` that yields every create, update, and delete on the table.

### subscribe_id(id) -- Single Record Changes

```rust,ignore
let mut rx = table.subscribe_id("order-123").await?;
while let Ok(msg) = rx.recv().await {
    println!("Order changed: {:?}", msg.data);
}
```

Returns a `broadcast::Receiver<SubscriptionMessage>` scoped to a specific record ID.

### publish(id, message) -- Custom Messages

```rust,ignore
table.publish("room-42", serde_json::json!({
    "type": "typing",
    "user": "alice"
})).await?;
```

Publishes a custom `Publish`-type message to the topic `"{table}/{id}"`. Useful for application-level events that are not tied to CRUD operations.

### Accessing PubSubManager Directly

For advanced use cases, access the `PubSubManager` directly:

```rust,ignore
let tables = context.tables();
if let Some(pubsub) = tables.pubsub() {
    let count = pubsub.topic_count().await;
    let subs = pubsub.subscriber_count("Message").await;
    let topics = pubsub.topics().await;
}
```

## Automatic CRUD Notifications

Every write on a `Table` automatically emits PubSub notifications.

| Operation | Notification |
|-----------|-------------|
| `table.put(id, data)` | `notify_update(table, id, data)` |
| `table.patch(id, data)` | `notify_update(table, id, merged)` |
| `table.create(data)` | `notify_update(table, auto_id, data)` |
| `table.delete(id)` | `notify_delete(table, id)` |

## Data Flow

```
REST PUT /User/123 {"name":"Updated"}
        |
        v
  Table::put() writes to storage
        |
        v
  pubsub_bridge::notify_update("User", "123", data)
        |
        +----> "User/123" topic -> record-level subscribers
        |
        +----> "User" topic -> table-level subscribers
                    |
                    +----> SSE stream -> EventSource clients
                    |
                    +----> WebSocket -> WS clients
                    |
                    +----> MQTT bridge -> MQTT subscribers
                    |
                    +----> Kafka producer -> Kafka topic
```

## PubSub Bridge (Dylib Safety)

Dylib plugins cannot directly call `PubSubManager` methods (`tokio::sync::broadcast::Sender::send()` locks a Mutex created in host context). The PubSub bridge uses 4 atomic function pointers:

- The host registers a C function pointer via `yeti_plugin_init`
- Plugin code calls `pubsub_bridge::notify_update()` / `notify_delete()`
- The bridge serializes the notification as JSON and calls through the pointer into host code
- The host deserializes and invokes the real `PubSubManager`

Transparent to application code -- the `Table` struct uses the bridge automatically.

## Kafka Producer Integration

The yeti-kafka service forwards table changes to Kafka topics by subscribing to PubSub and producing each change as JSON.

Configure in `yeti-config.yaml`:

```yaml
kafka:
  orders:
    brokers: "kafka-1:9092,kafka-2:9092"
    topic: "order-events"
    table: "Order"
    produce: true
```

Each change becomes a Kafka record:

```json
{
  "operation": "update",
  "table": "Order",
  "id": "order-123",
  "data": { "status": "shipped" },
  "timestamp": "2025-06-15T10:30:00Z"
}
```

See also: bidirectional Kafka bridging supports `consume: true` to ingest Kafka messages into Yeti tables.

## Performance

- **Zero-allocation short-circuit**: `notify_update()` and `notify_delete()` return immediately with no allocation when the topics map is empty or neither the record-level nor table-level topic has subscribers
- **Channel capacity**: Each topic uses a `tokio::sync::broadcast` channel with 256-message capacity. Slow consumers that fall behind lose older messages (lagged error)
- **Topic lifecycle**: Topics are created lazily on first `subscribe()`. Periodic cleanup (every 100 subscriptions) removes topics with zero active subscribers
- **DashMap concurrency**: Topics are stored in a `DashMap` for lock-free concurrent reads

## PubSubManager API Reference

| Method | Description |
|--------|-------------|
| `subscribe(topic)` | Subscribe, returns `broadcast::Receiver` |
| `publish(topic, message)` | Send to all subscribers, returns recipient count |
| `notify_update(table, id, data)` | Publish to record + table topics |
| `notify_delete(table, id)` | Publish deletion to both topics |
| `notify_publish(topic, data)` | Publish a custom message |
| `topic_count()` | Number of active topics |
| `subscriber_count(topic)` | Subscribers for a topic |
| `has_topic(topic)` | Check if topic exists |
| `remove_topic(topic)` | Remove topic, drop subscribers |
| `cleanup_empty_topics()` | Remove all zero-subscriber topics |
| `topics()` | List all active topic names |

## See Also

- [Real-Time Overview](realtime-overview.md) -- All real-time features
- [Server-Sent Events](sse.md) -- SSE delivery mechanism
- [WebSocket](websocket.md) -- WebSocket delivery mechanism
- [MQTT](mqtt.md) -- MQTT delivery mechanism

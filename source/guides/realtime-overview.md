# Real-Time Features

Four real-time mechanisms built on a shared PubSub backbone. Every table write publishes change events to all connected transports.

## Overview

| Feature | Direction | Protocol | Use Case |
|---------|-----------|----------|----------|
| [PubSub](pubsub.md) | Internal | In-process broadcast channels | Core event backbone for all real-time delivery |
| [SSE](sse.md) | Server to client | HTTP/1.1, HTTP/2 | Dashboards, notifications, feeds |
| [WebSocket](websocket.md) | Bidirectional | WS/WSS | Chat, collaboration, gaming |
| [MQTT](mqtt.md) | Bidirectional | MQTT 5 / MQTTS | IoT devices, sensors, M2M |

PubSub is the foundation. SSE, WebSocket, and MQTT are delivery transports that subscribe to PubSub topics.

## Real-Time Setup

Enable transports in your schema with the `@export` directive:

```graphql
type Message @table(database: "realtime-demo") @export(
    rest: true
    sse: true
    ws: true
    mqtt: true
) {
    id: ID! @primaryKey
    title: String!
    content: String!
}
```

## How It Works

1. Record created/updated/deleted via any write path (REST, GraphQL, SDK)
2. **PubSub** publishes to table-level topic (`"Message"`) and record-level topic (`"Message/msg-1"`)
3. SSE, WebSocket, and MQTT connections subscribed to those topics receive the update
4. Optional: Kafka producer bridges forward changes to external Kafka topics

```
Client A: POST /Message {"id":"msg-1","title":"Hello"}
                |
                v
         +-----------+
         |  PubSub   |  notify_update("Message", "msg-1", data)
         +-----------+
          /   |    \     \
         v    v     v     v
       SSE   WS   MQTT  Kafka
```

## Quick Example

**Terminal 1** -- subscribe via SSE:
```bash
curl -sk "https://localhost:9996/realtime-demo/message?stream=sse"
```

**Terminal 2** -- create a record:
```bash
curl -sk -X POST https://localhost:9996/realtime-demo/message \
  -H "Content-Type: application/json" \
  -d '{"id":"msg-1","title":"Hello","content":"Real-time works!"}'
```

## Topic Granularity

- **Table-level** (`/{table}?stream=sse`): all changes in the table
- **Record-level** (`/{table}/{id}?stream=sse`): changes to one record
- **Custom topics**: application code can publish to arbitrary topic strings via `table.publish(id, message)`

## PubSub Performance

PubSub short-circuits with zero allocation when no subscribers exist for a topic. Each topic uses a `tokio::sync::broadcast` channel with 256-message capacity. Topics are created lazily and cleaned up periodically (every 100 subscriptions) when subscriber count drops to zero.

## Sub-Guides

- [PubSub](pubsub.md) -- Internal messaging backbone
- [Server-Sent Events](sse.md) -- One-way streaming
- [WebSocket](websocket.md) -- Bidirectional communication
- [MQTT](mqtt.md) -- Native MQTT broker

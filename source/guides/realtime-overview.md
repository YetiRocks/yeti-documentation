# Real-Time Features

Yeti streams data changes to connected clients via SSE, WebSocket, and an internal PubSub backbone.

## Overview

| Feature | Direction | Protocol | Use Case |
|---------|-----------|----------|----------|
| [SSE](sse.md) | Server to client | HTTP/1.1, HTTP/2 | Dashboards, notifications, feeds |
| [WebSocket](websocket.md) | Bidirectional | WS/WSS | Chat, collaboration, gaming |
| [PubSub](pubsub.md) | Internal | In-process channels | Connects data changes to streams |

## Enabling Real-Time

Enable SSE and/or WebSocket in your schema:

```graphql
type Message @table(database: "realtime-demo") @export(
    rest: true
    sse: true
    ws: true
) {
    id: ID! @primaryKey
    title: String!
    content: String!
}
```

## How It Works

1. Record created/updated/deleted in a real-time table
2. **PubSub** publishes to table-level topic (`"Message"`) and record-level topic (`"Message/msg-1"`)
3. SSE and WebSocket connections receive the update

```
Client A: POST /Message {"id":"msg-1","title":"Hello"}
                |
                v
         +-----------+
         |  PubSub   |  notify_update("Message", "msg-1", data)
         +-----------+
           /        \
          v          v
   SSE clients    WS clients
```

## Quick Example

**Terminal 1** - subscribe:
```bash
curl -sk "https://localhost:9996/realtime-demo/message?stream=sse"
```

**Terminal 2** - create a record:
```bash
curl -sk -X POST https://localhost:9996/realtime-demo/message \
  -H "Content-Type: application/json" \
  -d '{"id":"msg-1","title":"Hello","content":"Real-time works!"}'
```

## Topic Granularity

- **Table-level** (`/{table}?stream=sse`): all changes in the table
- **Record-level** (`/{table}/{id}?stream=sse`): changes to one record

## Sub-Guides

- [Server-Sent Events](sse.md) - One-way streaming
- [WebSocket](websocket.md) - Bidirectional communication
- [PubSub](pubsub.md) - Internal messaging system
